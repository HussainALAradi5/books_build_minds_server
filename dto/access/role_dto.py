from dto.shared.base_entity_dto import BaseEntityDTO


class RoleDTO(BaseEntityDTO):
    key: str
    name: str
    description: str
    is_system: bool
    permission_keys: list[str]
