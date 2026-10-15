"""Receipt documents use immutable payment snapshots, never today's catalog price."""
from flask import g, send_file
from models.Book import Book
from models.receipts.Receipt import Receipt
from utils.responses import error
from utils.printing.receipt_pdf import render_receipt

def download_receipt(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    receipt = Receipt.query.filter_by(user_id=g.user.user_id, book_id=book.book_id,
        is_deleted=False, is_archived=False).filter(
            (Receipt.kind == "purchase") | Receipt.kind.is_(None)).order_by(Receipt.receipt_id.desc()).first()
    if not receipt:
        return error("No purchase receipt found", 403)
    return send_receipt(receipt)

def download_transaction_receipt(transaction):
    receipt = transaction.receipt
    if not receipt or transaction.status != "completed":
        return error("A receipt is available only after verified payment", 409)
    return send_receipt(receipt)

def send_receipt(receipt):
    return send_file(render_receipt(receipt), as_attachment=True,
        download_name=f"receipt-{receipt.receipt_id}.pdf", mimetype="application/pdf")
