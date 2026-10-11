"""Catalog and purchase operations."""
from datetime import datetime, timezone

from flask import g, jsonify, request
from slugify import slugify
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from config import db
from models.Book import Book
from models.Receipt import Receipt
from models.Review import Review
from utils.pagination import page_options, paginate
from utils.responses import error, success
from utils.validation import clean_text, json_body, positive_price, valid_date


def list_books():
    try:
        options = page_options()
        query = Book.query.options(selectinload(Book.reviews), selectinload(Book.loans))
        term = clean_text(request.args.get("q"), 120)
        if term:
            needle = f"%{term}%"
            query = query.filter(or_(Book.title.ilike(needle), Book.author.ilike(needle), Book.publisher.ilike(needle), Book.isbn.ilike(needle)))
        publisher = clean_text(request.args.get("publisher"), 120)
        if publisher:
            query = query.filter(Book.publisher.ilike(publisher))
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
            rating = db.session.query(Review.book_id, func.avg(Review.rating).label("score")).group_by(Review.book_id).subquery()
            query = query.outerjoin(rating, Book.book_id == rating.c.book_id).order_by(func.coalesce(rating.c.score, 0).desc(), Book.book_id.desc())
        elif sort == "title":
            query = query.order_by(Book.title.asc(), Book.book_id.asc())
        elif sort == "price_asc":
            query = query.order_by(Book.price.asc(), Book.book_id.asc())
        elif sort == "price_desc":
            query = query.order_by(Book.price.desc(), Book.book_id.desc())
        elif sort == "recent":
            query = query.order_by(Book.book_id.desc())
        else:
            raise ValueError("Unsupported sort")
        return jsonify(paginate(query, lambda book: book.to_summary_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def get_book(slug):
    book = Book.query.filter_by(slug=slug).first()
    return jsonify(book.to_dict()) if book else error("Book not found", 404)


def create_book():
    data = json_body()
    values = {key: clean_text(data.get(key), 255) for key in ("title", "isbn", "author", "publisher")}
    published = valid_date(data.get("published_at"))
    price = positive_price(data.get("price"))
    copies_total = data.get("copies_total", 1)
    if type(copies_total) is not int or not 1 <= copies_total <= 1000:
        return error("copies_total must be between 1 and 1000")
    if not all(values.values()) or not published or price is None:
        return error("Title, ISBN, author, publisher, publication date, and positive price are required")
    if Book.query.filter((Book.title == values["title"]) | (Book.isbn == values["isbn"])).first():
        return error("Title or ISBN already exists", 409)
    slug = slugify(values["title"])
    if not slug:
        return error("Title must contain letters or numbers")
    image = clean_text(data.get("book_image"), 500) or None
    if image and not (image.startswith("https://") or image.startswith("/static/covers/")):
        return error("Cover image must use HTTPS")
    book = Book(**values, slug=slug, book_image=image, published_at=published, price=price, copies_total=copies_total, added_by_user_id=g.user.user_id)
    db.session.add(book)
    db.session.commit()
    return success("Book added", 201, book=book.to_dict())


def purchase_book(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    if book in g.user.purchased_books:
        return error("Book already purchased", 409)
    receipt = Receipt(user_id=g.user.user_id, book_id=book.book_id, written_time=datetime.now(timezone.utc).date())
    g.user.purchased_books.append(book)
    db.session.add(receipt)
    db.session.commit()
    return success("Book purchased", book=book.to_dict(), receipt=receipt.to_dict())
