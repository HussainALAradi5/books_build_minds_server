from dto.shared.base_entity_dto import BaseEntityDTO


class UserAccessDTO(BaseEntityDTO):
    user_id: int
    user_name: str
    email: str
    role: str
    access_role_keys: list[str]
    group_ids: list[int]
    is_active: bool
