from dto.shared.base_entity_dto import BaseEntityDTO


class CountryDTO(BaseEntityDTO):
    code: str
    name: str
    flag_url: str | None
