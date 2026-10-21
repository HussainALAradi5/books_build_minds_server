"""Read-only printing and identification for visible catalog books."""
from flask import jsonify, send_file

from dto.books.book_codes_dto import BookCodesDTO
from enums.books.barcode_type import BarcodeType
from utils.books.book_lookup import visible_book
from utils.printing.book_codes import barcode_drawing, barcode_value, book_url, qr_drawing, svg_data_url
from utils.printing.book_pdf import render_book_pdf
from utils.shared.responses import error


def get_book_codes(slug: str):
    book = visible_book(slug)
    if not book:
        return error("Book not found", 404)
    url = book_url(book.slug)
    value = barcode_value(book.book_id)
    result: BookCodesDTO = {
        "book_id": book.book_id, "book_url": url, "barcode_value": value,
        "barcode_type": BarcodeType.CODE128.value,
        "qr_image": svg_data_url(qr_drawing(url)),
        "barcode_image": svg_data_url(barcode_drawing(value)),
    }
    return jsonify(result)


def download_book_pdf(slug: str):
    book = visible_book(slug)
    if not book:
        return error("Book not found", 404)
    return send_file(render_book_pdf(book), mimetype="application/pdf", as_attachment=True,
                     download_name=f"book-{book.book_id}.pdf")
