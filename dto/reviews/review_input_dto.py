from typing import TypedDict


class ReviewInputDTO(TypedDict):
    rating: float
    comment: str
    description: str
