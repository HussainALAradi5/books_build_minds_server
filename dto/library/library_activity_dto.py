from dto.shared.base_entity_dto import BaseEntityDTO

class LibraryActivityDTO(BaseEntityDTO):
    activity_id: int
    user_id: int
    book_id: int
    book_title: str
    book_slug: str
    action_type: str
    occurred_at: str
