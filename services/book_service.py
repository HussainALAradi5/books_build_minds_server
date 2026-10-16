"""Catalog and purchase operations."""
from flask import g, jsonify, request
from slugify import slugify
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from config import db
from models.Book import Book
from models.Author import Author
from models.Publisher import Publisher
from models.LibraryActivity import LibraryActivity
from models.reviews.Review import Review
from sqlalchemy.exc import IntegrityError
from utils.pagination import page_options, paginate, order_query
from utils.responses import error, success
from utils.validation import clean_text, json_body, positive_price, valid_date
from enums.books.book_status import BookStatus
from enums.library.library_action_type import LibraryActionType
from utils.book_events import emit_book_changed
from utils.book_lookup import visible_book
from utils.printing.book_codes import parse_barcode
from utils.book_input import normalize_book_input, resolve_catalog_people
from utils.inventory import has_open_work, occupied_copies, locked_book
from utils.tabular import export_table, import_table


def filtered_books(options, include_archived=False):
    query = Book.query.filter_by(is_deleted=False).options(selectinload(Book.reviews), selectinload(Book.loans))
    if not include_archived:
        query = query.filter_by(is_archived=False)
    term = clean_text(request.args.get("q"), 120)
    if term:
        needle = f"%{term}%"
        query = query.filter(or_(Book.book_id == parse_barcode(term), Book.title.ilike(needle), Book.author.ilike(needle), Book.publisher.ilike(needle), Book.isbn.ilike(needle)))
    publisher = clean_text(request.args.get("publisher"), 120)
    if publisher:
        query = query.filter(Book.publisher.ilike(publisher))
    condition = request.args.get("condition")
    if condition:
        if condition not in {item.value for item in BookStatus}:
            raise ValueError("Unsupported book condition")
        query = query.filter(Book.condition == condition)
    if request.args.get("min_price"):
        price = positive_price(request.args["min_price"])
        if price is None:
            raise ValueError("min_price must be positive")
        query = query.filter(Book.price >= price)
    if request.args.get("max_price"):
        price = positive_price(request.args["max_price"])
        if price is None:
            raise ValueError("max_price must be positive")
        query = query.filter(Book.price <= price)
    sort = request.args.get("sort", "recent")
    if sort == "rating":
        rating = db.session.query(Review.book_id, func.avg(Review.rating).label("score")).filter_by(is_deleted=False, is_archived=False).group_by(Review.book_id).subquery()
        return order_query(query.outerjoin(rating, Book.book_id == rating.c.book_id), func.coalesce(rating.c.score, 0), options, Book.book_id)
    if sort == "title":
        return order_query(query, Book.title, options, Book.book_id)
    if sort == "price":
        return order_query(query, Book.price, options, Book.book_id)
    if sort == "price_asc":
        return query.order_by(Book.price.asc(), Book.book_id.asc())
    if sort == "price_desc":
        return query.order_by(Book.price.desc(), Book.book_id.desc())
    if sort == "recent":
        return order_query(query, Book.book_id, options)
    raise ValueError("Unsupported sort")


def list_books():
    try:
        options = page_options()
        return jsonify(paginate(filtered_books(options), lambda book: book.to_summary_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def list_managed_books():
    try:
        options = page_options()
        return jsonify(paginate(filtered_books(options, include_archived=True), lambda book: book.to_summary_dict(), options))
    except ValueError as exc:
        return error(str(exc))


BOOK_EXPORT_COLUMNS = (
    ("book_id", "book_id"), ("title", "title"), ("isbn", "isbn"), ("author", "author"),
    ("publisher", "publisher"), ("published_at", "published_at"), ("price", "price"),
    ("copies_total", "copies_total"), ("condition", "condition"),
)
BOOK_IMPORT_COLUMNS = ("title", "isbn", "author", "publisher", "published_at", "price")


def export_books():
    try:
        options = page_options()
        query = filtered_books(options)
        selected = request.args.get("ids")
        if selected is not None:
            values = selected.split(",")
            if not 1 <= len(values) <= 100 or any(not value.isdigit() or int(value) < 1 for value in values):
                raise ValueError("Select between 1 and 100 valid book IDs")
            query = query.filter(Book.book_id.in_([int(value) for value in values]))
        books = query.limit(5000).all()
        rows = [book.to_summary_dict() for book in books]
        return export_table(BOOK_EXPORT_COLUMNS, rows, request.args.get("format", "xlsx"), "library-books")
    except ValueError as exc:
        return error(str(exc))


def import_books():
    try:
        rows = import_table(request.files.get("file"), BOOK_IMPORT_COLUMNS)
        imported = []
        for number, row in enumerate(rows, start=2):
            try:
                if hasattr(row.get("published_at"), "isoformat"):
                    row["published_at"] = row["published_at"].date().isoformat() if hasattr(row["published_at"], "date") else row["published_at"].isoformat()
                values = normalize_book_input(row)
                if Book.query.filter((Book.title == values["title"]) | (Book.isbn == values["isbn"])).first():
                    raise ValueError("Title or ISBN already exists")
                slug = slugify(values["title"])
                if not slug:
                    raise ValueError("Title must contain letters or numbers")
                author, publisher = resolve_catalog_people(values["author"], values["publisher"])
                book = Book(**values, slug=slug, author_id=author.author_id,
                            publisher_id=publisher.publisher_id, added_by_user_id=g.user.user_id)
                db.session.add(book)
                db.session.flush()
                imported.append(book.book_id)
            except (ValueError, IntegrityError) as exc:
                db.session.rollback()
                return error(f"Row {number}: {exc}", 400)
        db.session.commit()
        return success("Books imported", 201, count=len(imported), book_ids=imported)
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        db.session.rollback()
        return error(str(exc))


def bulk_books():
    data = json_body()
    ids = data.get("ids")
    action = data.get("action")
    if not isinstance(ids, list) or not ids or len(ids) > 100 or any(type(item) is not int for item in ids):
        return error("Select 1 to 100 book IDs")
    if action not in ("archive", "unarchive", "delete"):
        return error("Unsupported bulk action")
    books = Book.query.filter(Book.book_id.in_(ids), Book.is_deleted.is_(False)).order_by(Book.book_id).with_for_update().all()
    if len(books) != len(set(ids)):
        return error("One or more books were not found", 404)
    for book in books:
        if action in ("delete", "archive") and has_open_work(book):
            return error("Resolve active loans and pending checkouts before archiving or deleting books", 409)
    for book in books:
        if action == "archive":
            book.is_archived = True
        elif action == "unarchive":
            book.is_archived = False
        else:
            book.is_deleted = True
    db.session.commit()
    for book in books:
        emit_book_changed(book.slug, "book")
    return success("Books updated", count=len(books))


def get_book(slug):
    book = visible_book(slug)
    return jsonify(book.to_dict()) if book else error("Book not found", 404)


def create_book():
    try:
        values = normalize_book_input(json_body())
    except ValueError as exc:
        return error(str(exc))
    if Book.query.filter((Book.title == values["title"]) | (Book.isbn == values["isbn"])).first():
        return error("Title or ISBN already exists", 409)
    slug = slugify(values["title"])
    if not slug:
        return error("Title must contain letters or numbers")
    author, publisher = resolve_catalog_people(values["author"], values["publisher"])
    book = Book(**values, slug=slug, author_id=author.author_id, publisher_id=publisher.publisher_id, added_by_user_id=g.user.user_id)
    db.session.add(book)
    db.session.commit()
    return success("Book added", 201, book=book.to_dict())


def update_book(slug):
    candidate = visible_book(slug)
    book = locked_book(candidate.book_id) if candidate else None
    if not book:
        return error("Book not found", 404)
    data = json_body()
    for field in ("title", "isbn"):
        if field in data:
            value = clean_text(data[field], 255)
            if not value:
                return error(f"{field} is required")
            duplicate = Book.query.filter(getattr(Book, field) == value, Book.book_id != book.book_id).first()
            if duplicate:
                return error(f"{field} already exists", 409)
            setattr(book, field, value)
    for field, model, id_field in (("author", Author, "author_id"), ("publisher", Publisher, "publisher_id")):
        if field in data:
            name = clean_text(data[field], 255)
            if not name:
                return error(f"{field} is required")
            record = model.query.filter_by(name=name, is_deleted=False).first()
            if not record:
                record = model(name=name, description="")
                db.session.add(record)
                db.session.flush()
            setattr(book, field, name)
            setattr(book, id_field, getattr(record, id_field))
    if "published_at" in data:
        published = valid_date(data["published_at"])
        if not published:
            return error("Invalid publication date")
        book.published_at = published
    if "price" in data:
        price = positive_price(data["price"])
        if price is None:
            return error("Price must be positive")
        book.price = price
    if "copies_total" in data:
        copies = data["copies_total"]
        if type(copies) is not int or not 1 <= copies <= 1000:
            return error("copies_total must be between 1 and 1000")
        if copies < occupied_copies(book):
            return error("Copies cannot be fewer than sales, active loans, and reserved stock")
        book.copies_total = copies
    if "condition" in data:
        if data["condition"] not in {item.value for item in BookStatus}:
            return error("Unsupported book condition")
        book.condition = data["condition"]
    if "book_image" in data:
        image = clean_text(data["book_image"], 500) or None
        if image and not (image.startswith("https://") or image.startswith("/static/covers/")):
            return error("Cover image must use HTTPS")
        book.book_image = image
    db.session.commit()
    emit_book_changed(slug, "book")
    return success("Book updated", book=book.to_dict())


def delete_book(slug):
    candidate = visible_book(slug)
    book = locked_book(candidate.book_id) if candidate else None
    if not book:
        return error("Book not found", 404)
    if has_open_work(book):
        return error("Resolve active loans and pending checkouts before deleting this book", 409)
    book.is_deleted = True
    db.session.commit()
    emit_book_changed(slug, "book")
    return success("Book deleted")


def purchase_book(slug):
    return error("Use verified payment checkout for purchases", 409)
