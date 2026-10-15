from typing import TypedDict

class LoanQuoteDTO(TypedDict):
    book_title: str
    available_copies: int
    borrow_days: int
    rental_days: int
    rental_amount_minor: int
    purchase_amount_minor: int
    currency: str
    currency_scale: int
    policy_version: str
    terms: list[str]
