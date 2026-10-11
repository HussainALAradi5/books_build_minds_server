"""Generate a receipt only for the authenticated purchaser."""
from datetime import datetime, timezone
from io import BytesIO

from flask import g, send_file
from reportlab.pdfgen import canvas

from models.Book import Book
from models.receipts.Receipt import Receipt
from utils.responses import error


def create_purchase_receipt(user_id: int, book_id: int) -> Receipt:
    return Receipt(user_id=user_id, book_id=book_id, written_time=datetime.now(timezone.utc).date())


def download_receipt(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    receipt = Receipt.query.filter_by(
        user_id=g.user.user_id, book_id=book.book_id, is_deleted=False, is_archived=False
    ).first()
    if not receipt:
        return error("You have not purchased this book", 403)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setTitle("Book purchase receipt")
    rows = [
        "Books Build Minds — Purchase Receipt",
        f"Receipt ID: {receipt.receipt_id}",
        f"Book: {book.title}",
        f"Author: {book.author}",
        f"Price: {book.price:.2f} BHD",
        f"Purchased by: {g.user.user_name}",
        f"Date: {receipt.written_time.isoformat()}",
    ]
    for index, line in enumerate(rows):
        pdf.drawString(72, 760 - index * 30, line)
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="receipt.pdf", mimetype="application/pdf")
