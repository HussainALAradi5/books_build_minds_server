from dto.shared.base_entity_dto import BaseEntityDTO
from dto.receipts.receipt_dto import ReceiptDTO

class UserDTO(BaseEntityDTO):
    user_id: int
    user_name: str
    email: str
    mobile_number: str | None
    is_active: bool
    role: str
    permissions: list[str]
    purchased_books: list[int]
    receipts: list[ReceiptDTO]
    profile_picture_url: str | None
