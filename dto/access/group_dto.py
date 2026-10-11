from dto.shared.base_entity_dto import BaseEntityDTO


class GroupDTO(BaseEntityDTO):
    group_id: int
    name: str
    description: str
    role_keys: list[str]
    member_count: int
