from dto.books.book_summary_dto import BookSummaryDTO
from dto.catalog.author_dto import AuthorDTO
from dto.catalog.publisher_dto import PublisherDTO
from dto.reviews.review_dto import ReviewDTO
from dto.media.media_dto import MediaDTO

class BookDTO(BookSummaryDTO):
    description: str
    reviews: list[ReviewDTO]
    added_by_user_id: int
    purchased_by: list[int]
    media: list[MediaDTO]
    author_details: AuthorDTO | None
    publisher_details: PublisherDTO | None
