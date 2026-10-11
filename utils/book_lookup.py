from models.Book import Book


def visible_book(slug: str) -> Book | None:
    return Book.query.filter_by(slug=slug, is_deleted=False, is_archived=False).first()
