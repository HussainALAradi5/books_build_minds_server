from dto.shared.base_entity_dto import BaseEntityDTO

class AdminRequestDTO(BaseEntityDTO):
    request_id: int
    is_accepted: bool | None
    review_time: str | None
    reviewed_by_user_id: int | None
    reason_for_request: str
    requester_id: int
