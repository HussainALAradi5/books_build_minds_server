"""Public print endpoints expose only visible catalog metadata."""
import os
import unittest
from base64 import b64decode
from datetime import date
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-long-enough-for-hs256"

from app import app
from config import db
from models.catalog.Book import Book
from models.accounts.User import User
from utils.printing.book_codes import book_url


class BookPrintTests(unittest.TestCase):
    def setUp(self):
        from app import limiter
        limiter.enabled = False
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        user = User(user_name="print-reader", email="print@example.test", password_digest="unused")
        db.session.add(user)
        db.session.flush()
        self.book = Book(title="A & B <Library>", slug="print-book", isbn="9780140328721",
                         author="An Author", publisher="A Press", published_at=date(2020, 1, 1),
                         price=5, added_by_user_id=user.user_id)
        db.session.add(self.book)
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_codes_use_configured_url_and_stable_identifier(self):
        with patch.dict(app.config, PUBLIC_CLIENT_URL="https://library.example"):
            response = self.client.get("/api/book/print-book/codes", headers={"Host": "untrusted.example"})
        self.assertEqual(response.status_code, 200)
        codes = response.json
        self.assertEqual(codes["book_url"], "https://library.example/book/print-book")
        self.assertEqual(codes["barcode_value"], f"BBM-{self.book.book_id:08d}")
        self.assertEqual(codes["barcode_type"], "Code128")
        for key in ("qr_image", "barcode_image"):
            image = b64decode(codes[key].split(",", 1)[1])
            self.assertIn(b"<svg", image)
            self.assertNotIn(b"<script", image)
        original = codes["barcode_value"]
        self.book.isbn = "changed-isbn"
        db.session.commit()
        self.assertEqual(self.client.get("/api/book/print-book/codes").json["barcode_value"], original)
        self.assertEqual(self.client.get(f"/api/?q={original}").json["pagination"]["total"], 1)

    def test_pdf_is_downloadable_without_modifying_book(self):
        response = self.client.get("/api/book/print-book/print")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF-"))
        self.assertIn(f"book-{self.book.book_id}.pdf", response.headers["Content-Disposition"])
        self.assertEqual(Book.query.count(), 1)

    def test_hidden_and_missing_books_have_no_print_or_codes(self):
        for suffix in ("codes", "print"):
            self.assertEqual(self.client.get(f"/api/book/missing/{suffix}").status_code, 404)
        for flag in ("is_archived", "is_deleted"):
            setattr(self.book, flag, True)
            db.session.commit()
            for suffix in ("codes", "print"):
                self.assertEqual(self.client.get(f"/api/book/print-book/{suffix}").status_code, 404)
            setattr(self.book, flag, False)
            db.session.commit()

    def test_unsafe_qr_origin_is_rejected(self):
        for url in ("javascript:alert(1)", "https://user:secret@example.test", "https://example.test/?x=1"):
            with patch.dict(app.config, PUBLIC_CLIENT_URL=url):
                with self.assertRaises(ValueError):
                    book_url("print-book")
