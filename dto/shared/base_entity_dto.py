from typing import TypedDict


class BaseEntityDTO(TypedDict):
    created_by: int | None
    created_at: str
    updated_by: int | None
    updated_at: str | None
    is_archived: bool
    is_deleted: bool
