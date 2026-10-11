"""Regression tests for previously exposed authorization paths."""
import os
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-long-enough-for-hs256"

from app import app  # noqa: E402
from config import db  # noqa: E402
from models.Book import Book  # noqa: E402
from models.reviews.Review import Review  # noqa: E402
from models.User import User  # noqa: E402
from models.Media import Media  # noqa: E402
from models.Loan import Loan  # noqa: E402
from models.LibraryActivity import LibraryActivity  # noqa: E402
from enums.media.media_type import MediaType  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402
from utils.security import create_token  # noqa: E402
from services import media_service  # noqa: E402
from config import BASE_DIR  # noqa: E402


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        self.user = User(user_name="reader", email="reader@example.test", password_digest=generate_password_hash("reader12345"), is_admin=False, is_active=True)
        self.other = User(user_name="other", email="other@example.test", password_digest=generate_password_hash("other12345"), is_admin=False, is_active=True)
        db.session.add_all([self.user, self.other])
        db.session.flush()
        self.book = Book(title="One Book", isbn="111", slug="one-book", author="Author", publisher="Press", published_at=date(2020, 1, 1), price=5, added_by_user_id=self.user.user_id)
        self.other_book = Book(title="Other Book", isbn="222", slug="other-book", author="Author", publisher="Press", published_at=date(2020, 1, 1), price=5, added_by_user_id=self.user.user_id)
        db.session.add_all([self.book, self.other_book])
        db.session.commit()
        self.client = app.test_client()
        self.headers = {"Authorization": f"Bearer {create_token(self.user)}"}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_profile_cannot_grant_admin(self):
        response = self.client.put(f"/api/profile/{self.user.user_id}/edit", headers=self.headers, json={"is_admin": True})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(db.session.get(User, self.user.user_id).is_admin)

    def test_profile_cannot_read_other_user(self):
        response = self.client.get(f"/api/profile/{self.other.user_id}", headers=self.headers)
        self.assertEqual(response.status_code, 403)

    def test_review_id_must_match_book_slug(self):
        review = Review(user_id=self.user.user_id, book_id=self.book.book_id, rating=5, comment="Great reading", written_time=date.today())
        db.session.add(review)
        db.session.commit()
        response = self.client.delete(f"/api/book/other-book/review/{review.review_id}", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIsNotNone(db.session.get(Review, review.review_id))

    def test_receipt_requires_authenticated_owner(self):
        response = self.client.get("/api/book/one-book/receipt")
        self.assertEqual(response.status_code, 401)
        response = self.client.get("/api/book/one-book/receipt", headers=self.headers)
        self.assertEqual(response.status_code, 403)

    def test_catalog_filters_and_paginates(self):
        response = self.client.get("/api/?page=1&per_page=1&sort=title")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["items"]), 1)
        self.assertEqual(response.json["pagination"]["total"], 2)
        response = self.client.get("/api/?q=Other&min_price=1")
        self.assertEqual(response.json["pagination"]["total"], 1)
        self.assertEqual(response.json["items"][0]["slug"], "other-book")

    def test_multiple_media_upload_is_server_validated(self):
        self.user.is_admin = True
        db.session.commit()
        buffer = BytesIO()
        Image.new("RGB", (8, 8), "red").save(buffer, format="PNG")
        payload = buffer.getvalue()
        with TemporaryDirectory(dir=BASE_DIR) as directory, patch.object(media_service, "MEDIA_DIR", Path(directory)):
            response = self.client.post(f"/api/media/books/{self.book.book_id}", headers=self.headers,
                                        data={"files": [(BytesIO(payload), "first.png"), (BytesIO(payload), "second.png")]},
                                        content_type="multipart/form-data")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(len(response.json["items"]), 2)
            self.assertEqual(Media.query.filter_by(book_id=self.book.book_id).count(), 2)
            self.assertEqual(response.json["items"][0]["media_type"], MediaType.BOOK_COVER.value)
            listing = self.client.get(f"/api/media/books/{self.book.book_id}?per_page=1")
            self.assertEqual(listing.json["pagination"]["pages"], 2)

    def test_profile_picture_is_owned_and_typed(self):
        buffer = BytesIO()
        Image.new("RGB", (8, 8), "blue").save(buffer, format="PNG")
        with TemporaryDirectory(dir=BASE_DIR) as directory, patch.object(media_service, "MEDIA_DIR", Path(directory)):
            response = self.client.post("/api/media/profile-picture", headers=self.headers,
                                        data={"files": (BytesIO(buffer.getvalue()), "avatar.png")},
                                        content_type="multipart/form-data")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json["media"]["media_type"], MediaType.PROFILE_PICTURE.value)
            self.assertEqual(response.json["media"]["user_id"], self.user.user_id)
            self.assertTrue(response.json["user"]["profile_picture_url"])
            self.assertEqual(self.client.get(f"/api/profile/{self.user.user_id}", headers=self.headers).json["profile_picture_url"], response.json["media"]["url"])

    def test_borrow_return_and_availability(self):
        self.book.copies_total = 1
        db.session.commit()
        borrowed = self.client.post("/api/book/one-book/borrow", headers=self.headers)
        self.assertEqual(borrowed.status_code, 201)
        self.assertEqual(borrowed.json["loan"]["status"], "active")
        self.assertEqual(self.client.get("/api/book/one-book").json["available_copies"], 0)
        other_headers = {"Authorization": f"Bearer {create_token(self.other)}"}
        self.assertEqual(self.client.post("/api/book/one-book/borrow", headers=other_headers).status_code, 409)
        self.assertEqual(self.client.get(f"/api/profile/{self.user.user_id}/loans", headers=other_headers).status_code, 403)
        self.assertEqual(self.client.get(f"/api/profile/{self.user.user_id}/loans?status=active", headers=self.headers).json["pagination"]["total"], 1)
        returned = self.client.post("/api/book/one-book/return", headers=self.headers)
        self.assertEqual(returned.status_code, 200)
        self.assertEqual(returned.json["loan"]["status"], "returned")
        self.assertEqual(self.client.get("/api/book/one-book").json["available_copies"], 1)
        self.assertEqual(Loan.query.count(), 1)

    def test_admin_access_is_reviewed_through_account_api(self):
        submitted = self.client.post("/api/admin-requests", headers=self.headers,
                                     json={"reason_for_request": "I can manage the library catalog."})
        self.assertEqual(submitted.status_code, 201)
        request_id = submitted.json["request"]["request_id"]
        self.assertEqual(self.client.get("/api/admin-requests", headers=self.headers).status_code, 403)
        self.other.is_admin = True
        db.session.commit()
        admin_headers = {"Authorization": f"Bearer {create_token(self.other)}"}
        self.assertEqual(self.client.get("/api/admin-requests?status=pending", headers=admin_headers).json["pagination"]["total"], 1)
        reviewed = self.client.patch(f"/api/admin-requests/{request_id}", headers=admin_headers,
                                     json={"is_accepted": True})
        self.assertEqual(reviewed.status_code, 200)
        self.assertTrue(db.session.get(User, self.user.user_id).is_admin)

    def test_condition_and_action_history_are_typed(self):
        self.assertEqual(self.client.get("/api/book/one-book").json["condition"], "good")
        self.assertEqual(self.client.post("/api/book/one-book/borrow", headers=self.headers).status_code, 201)
        self.assertEqual(self.client.post("/api/book/one-book/return", headers=self.headers).status_code, 200)
        self.assertEqual(self.client.post("/api/book/one-book/purchase", headers=self.headers).status_code, 200)
        listing = self.client.get(f"/api/profile/{self.user.user_id}/activities?action=borrow", headers=self.headers)
        self.assertEqual(listing.json["pagination"]["total"], 1)
        self.assertEqual(listing.json["items"][0]["action_type"], "borrow")
        self.assertEqual(LibraryActivity.query.count(), 4)
        self.assertEqual(self.client.get(f"/api/profile/{self.other.user_id}/activities", headers=self.headers).status_code, 403)


if __name__ == "__main__":
    unittest.main()
