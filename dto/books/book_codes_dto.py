from typing import TypedDict


class BookCodesDTO(TypedDict):
    book_id: int
    book_url: str
    barcode_value: str
    barcode_type: str
    qr_image: str
    barcode_image: str
