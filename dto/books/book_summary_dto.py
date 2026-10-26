from dto.shared.base_entity_dto import BaseEntityDTO
from dto.catalog.category_dto import CategoryDTO

class BookSummaryDTO(BaseEntityDTO):
    book_id: int
    isbn: str
    book_image: str | None
    slug: str
    title: str
    author: str
    publisher: str
    categories: list[CategoryDTO]
    published_at: str
    price: float
    average_rating: float
    copies_total: int
    available_copies: int
    condition: str
