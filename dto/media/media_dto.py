from dto.shared.base_entity_dto import BaseEntityDTO

class MediaDTO(BaseEntityDTO):
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
