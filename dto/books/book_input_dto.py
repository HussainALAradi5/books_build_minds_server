from datetime import date
from typing import TypedDict


class BookInputDTO(TypedDict):
    title: str
    description: str
    isbn: str
    author: str
    publisher: str
    category_ids: list[int]
    published_at: date
    price: float
    copies_total: int
    condition: str
    book_image: str | None
