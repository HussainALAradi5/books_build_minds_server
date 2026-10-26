from dto.shared.base_entity_dto import BaseEntityDTO


class CategoryDTO(BaseEntityDTO):
    category_id: int
    name: str
    slug: str
