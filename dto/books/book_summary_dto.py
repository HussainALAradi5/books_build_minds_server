from dto.shared.base_entity_dto import BaseEntityDTO

class BookSummaryDTO(BaseEntityDTO):
    book_id: int
    isbn: str
    book_image: str | None
    slug: str
    title: str
    author: str
    publisher: str
    published_at: str
    price: float
    average_rating: float
    copies_total: int
    available_copies: int
    condition: str
