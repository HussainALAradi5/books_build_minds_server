from flask import jsonify
from constants.library_policy import BORROW_DAYS, RENTAL_DAYS, POLICY_VERSION, CURRENCY, CURRENCY_SCALE
from dto.library.loan_quote_dto import LoanQuoteDTO
from utils.book_lookup import visible_book
from utils.payments.money import price_minor
from utils.responses import error

def loan_quote(slug):
    book = visible_book(slug)
    if not book:
        return error("Book not found", 404)
    quote: LoanQuoteDTO = {"book_title": book.title, "available_copies": book.available_copies,
        "borrow_days": BORROW_DAYS, "rental_days": RENTAL_DAYS,
        "rental_amount_minor": price_minor(book.price, True), "purchase_amount_minor": price_minor(book.price),
        "currency": CURRENCY, "currency_scale": CURRENCY_SCALE, "policy_version": POLICY_VERSION,
        "terms": ["Borrowed and rented books must be returned by the due date.",
                  "Check the book condition before collecting it and report damage to staff.",
                  "A paid rental starts only after verified payment. Borrowing is free.",
                  "Stock is checked again when you confirm; availability may change."]}
    return jsonify(quote)
