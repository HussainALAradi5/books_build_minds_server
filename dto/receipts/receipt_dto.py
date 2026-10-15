from dto.shared.base_entity_dto import BaseEntityDTO

class ReceiptDTO(BaseEntityDTO):
    receipt_id: int
    transaction_id: str | None
    amount_minor: int | None
    currency: str | None
    currency_scale: int | None
    user_id: int
    book_id: int
    written_time: str
