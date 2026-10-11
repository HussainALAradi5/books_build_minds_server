"""Public JSON contract. Mirrors client/src/lib/types.ts."""
from typing import Generic, NotRequired, TypeVar, TypedDict

T = TypeVar("T")


class PaginationDTO(TypedDict):
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_previous: bool


class PageDTO(TypedDict, Generic[T]):
    items: list[T]
    pagination: PaginationDTO


class ReviewDTO(TypedDict):
    review_id: int
    user_id: int
    user_name: str
    book_id: int
    comment: str
    written_time: str
    last_edit: str | None
    rating: float


class ReceiptDTO(TypedDict):
    receipt_id: int
    user_id: int
    book_id: int
    written_time: str


class MediaDTO(TypedDict):
    media_id: int
    book_id: int | None
    user_id: int | None
    media_type: str
    uploaded_by_user_id: int
    original_name: str
    mime_type: str
    size_bytes: int
    uploaded_at: str
    url: str


class BookSummaryDTO(TypedDict):
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


class BookDTO(BookSummaryDTO):
    reviews: list[ReviewDTO]
    added_by_user_id: int
    purchased_by: list[int]
    media: list[MediaDTO]


class BookCreateDTO(TypedDict):
    title: str
    isbn: str
    author: str
    publisher: str
    published_at: str
    price: float
    copies_total: int
    book_image: NotRequired[str | None]


class UserDTO(TypedDict):
    user_id: int
    user_name: str
    email: str
    is_admin: bool
    is_active: bool
    purchased_books: list[int]
    receipts: list[ReceiptDTO]
    profile_picture_url: str | None


class LoanDTO(TypedDict):
    loan_id: int
    user_id: int
    book_id: int
    book_title: str
    book_slug: str
    borrowed_at: str
    due_at: str
    returned_at: str | None
    status: str


class AdminRequestDTO(TypedDict):
    request_id: int
    is_accepted: bool | None
    review_time: str | None
    reviewed_by_user_id: int | None
    reason_for_request: str
    requester_id: int


class ErrorDTO(TypedDict):
    error: str


class MessageDTO(TypedDict):
    message: str


class LoginDTO(MessageDTO):
    token: str
    user_id: int


class BookResultDTO(MessageDTO):
    book: BookDTO
    receipt: NotRequired[ReceiptDTO]
