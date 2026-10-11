from dto.shared.base_entity_dto import BaseEntityDTO


class PermissionDTO(BaseEntityDTO):
    key: str
    label: str
    description: str
    is_system: bool
