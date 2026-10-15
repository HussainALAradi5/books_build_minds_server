from dto.shared.base_entity_dto import BaseEntityDTO

class TransactionDTO(BaseEntityDTO):
    transaction_id: str
    book_id: int
    book_title: str
    book_slug: str
    kind: str
    status: str
    amount_minor: int
    currency: str
    currency_scale: int
    paid_at: str | None
    checkout_url: str | None
    receipt_id: int | None
    failure_reason: str | None
