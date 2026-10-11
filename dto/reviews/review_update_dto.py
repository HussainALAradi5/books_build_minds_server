from typing import TypedDict


class ReviewUpdateDTO(TypedDict, total=False):
    rating: float
    comment: str
    description: str
