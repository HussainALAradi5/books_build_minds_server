from dto.shared.base_entity_dto import BaseEntityDTO

class ReceiptDTO(BaseEntityDTO):
    receipt_id: int
    user_id: int
    book_id: int
    written_time: str
