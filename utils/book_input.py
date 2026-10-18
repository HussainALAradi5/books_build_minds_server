"""Validation and relationship resolution shared by single and bulk book creation."""
from config import db
from dto.books.book_input_dto import BookInputDTO
from dto.books.book_price_input_dto import BookPriceInputDTO
from enums.books.book_status import BookStatus
from models.Author import Author
from models.Publisher import Publisher
from utils.validation import clean_text, positive_price, valid_date


def normalize_book_input(data) -> BookInputDTO:
    values = {key: clean_text(data.get(key), 255) for key in ("title", "isbn", "author", "publisher")}
    published = valid_date(data.get("published_at"))
    price = positive_price(data.get("price"))
    copies_raw = data.get("copies_total", 1)
    try:
        copies_total = int(copies_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("copies_total must be between 1 and 1000") from exc
    condition = data.get("condition") or BookStatus.GOOD.value
    if condition not in {item.value for item in BookStatus}:
        raise ValueError("Unsupported book condition")
    if not 1 <= copies_total <= 1000:
        raise ValueError("copies_total must be between 1 and 1000")
    if not all(values.values()) or not published or price is None:
        raise ValueError("Title, ISBN, author, publisher, publication date, and positive price are required")
    image = clean_text(data.get("book_image"), 500) or None
    if image and not (image.startswith("https://") or image.startswith("/static/covers/")):
        raise ValueError("Cover image must use HTTPS")
    return {**values, "published_at": published, "price": price, "copies_total": copies_total,
            "condition": condition, "book_image": image}


def normalize_book_price_input(data: object) -> BookPriceInputDTO:
    if not isinstance(data, dict) or set(data) != {"price"}:
        raise ValueError("Only price can be edited after a book is created")
    price = positive_price(data["price"])
    if price is None:
        raise ValueError("Price must be positive")
    return {"price": price}


def resolve_catalog_people(author_name: str, publisher_name: str):
    author = Author.query.filter_by(name=author_name, is_deleted=False).first()
    publisher = Publisher.query.filter_by(name=publisher_name, is_deleted=False).first()
    if not author:
        author = Author(name=author_name, description="")
        db.session.add(author)
    if not publisher:
        publisher = Publisher(name=publisher_name, description="")
        db.session.add(publisher)
    db.session.flush()
    return author, publisher
