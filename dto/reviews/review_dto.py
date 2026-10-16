from dto.shared.base_entity_dto import BaseEntityDTO

class ReviewDTO(BaseEntityDTO):
    review_id: int
    user_id: int
    user_name: str
    profile_picture_url: str | None
    book_id: int
    comment: str
    description: str
    written_time: str
    last_edit: str | None
    rating: float
