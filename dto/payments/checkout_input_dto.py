from typing import TypedDict

class CheckoutInputDTO(TypedDict):
    book_slug: str
    kind: str
    request_key: str
    expected_amount_minor: int
    accepted_terms: bool
    policy_version: str
