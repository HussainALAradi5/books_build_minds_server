from dto.shared.base_entity_dto import BaseEntityDTO

from dto.catalog.country_dto import CountryDTO
from dto.catalog.work_dto import WorkDTO


class AuthorDTO(BaseEntityDTO):
    author_id: int
    name: str
    description: str
    country: CountryDTO | None
    works: list[WorkDTO]
