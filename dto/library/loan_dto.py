from dto.shared.base_entity_dto import BaseEntityDTO

class LoanDTO(BaseEntityDTO):
    loan_id: int
    user_id: int
    book_id: int
    book_title: str
    book_slug: str
    borrowed_at: str
    due_at: str
    returned_at: str | None
    status: str
    loan_kind: str
    rental_fee: float
