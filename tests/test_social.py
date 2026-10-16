"""Social features and catalog administration regression tests."""
import os
import unittest
from datetime import date
from io import BytesIO
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-long-enough-for-hs256"

from payment_fixture import pay
from constants.library_policy import POLICY_VERSION
from app import app, socketio  # noqa: E402
from config import db  # noqa: E402
from models.Author import Author  # noqa: E402
from models.Book import Book  # noqa: E402
from models.reviews.Review import Review  # noqa: E402
from models.Country import Country  # noqa: E402
from models.User import User  # noqa: E402
from enums.accounts.account_role import AccountRole  # noqa: E402
from enums.accounts.permission import Permission  # noqa: E402
from utils.access import all_of, any_of, has_access, owns  # noqa: E402
from utils.security import create_token  # noqa: E402
from seed_demo import TEST_PASSWORDS  # noqa: E402


class SocialTests(unittest.TestCase):
    def setUp(self):
        from app import limiter
        limiter.enabled = False
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        self.reader = User(user_name="reader", email="reader@example.test", password_digest="hash", is_active=True)
        self.other = User(user_name="other", email="other@example.test", password_digest="hash", is_active=True)
        self.admin = User(user_name="admin", email="admin@example.test", password_digest="hash", is_active=True, is_admin=True)
        db.session.add_all([self.reader, self.other, self.admin])
        db.session.flush()
        self.book = Book(title="A Book", slug="a-book", isbn="isbn", author="Writer", publisher="Press",
                         published_at=date(2020, 1, 1), price=5, added_by_user_id=self.admin.user_id)
        db.session.add(self.book)
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def headers(self, user):
        return {"Authorization": f"Bearer {create_token(user)}"}

    def test_member_export_selection_and_admin_only_import(self):
        from openpyxl import load_workbook
        second = Book(title="Another Book", slug="another-book", isbn="another-isbn", author="Writer",
                      publisher="Press", published_at=date(2022, 1, 1), price=7,
                      added_by_user_id=self.admin.user_id)
        db.session.add(second)
        db.session.commit()
        response = self.client.get(f"/api/book/export?format=xlsx&ids={self.book.book_id}",
                                   headers=self.headers(self.reader))
        self.assertEqual(response.status_code, 200)
        rows = list(load_workbook(BytesIO(response.data), read_only=True).active.values)
        self.assertEqual(len(rows), 2)
        self.assertIn("A Book", rows[1])
        self.assertEqual(self.client.get("/api/book/export?format=xlsx&ids=abc",
                          headers=self.headers(self.reader)).status_code, 400)
        self.assertEqual(self.client.post("/api/book/import", headers=self.headers(self.reader)).status_code, 403)

    def test_documented_demo_accounts_login_with_expected_roles(self):
        result = app.test_cli_runner().invoke(args=["seed-demo", "--test-accounts"])
        self.assertEqual(result.exit_code, 0, result.output)
        from seed_demo import BOOKS
        from models.Publisher import Publisher
        for _, isbn, _, _, _, _ in BOOKS:
            seeded = Book.query.filter_by(isbn=isbn).one()
            self.assertIsNotNone(seeded.author_id)
            self.assertIsNotNone(seeded.publisher_id)
        before = Publisher.query.count()
        rerun = app.test_cli_runner().invoke(args=["seed-demo"])
        self.assertEqual(rerun.exit_code, 0, rerun.output)
        self.assertEqual(Publisher.query.count(), before)
        for username, role in (("demo_admin", AccountRole.ADMIN),
                               ("demo_employee", AccountRole.EMPLOYEE),
                               ("demo_client", AccountRole.CLIENT)):
            response = self.client.post("/api/login", json={
                "user_name_or_email": username, "password": TEST_PASSWORDS[username],
            })
            self.assertEqual(response.status_code, 200, username)
            self.assertEqual(User.query.filter_by(user_name=username).one().role, role)
        visitor = User.query.filter_by(user_name="demo_visitor").one()
        self.assertFalse(visitor.is_active)

    def test_only_purchaser_can_review_and_owner_or_admin_can_manage(self):
        review_path = "/api/book/a-book/review"
        payload = {"rating": 5, "comment": "A thoughtful review", "description": "A longer description"}
        self.assertEqual(self.client.post(review_path, headers=self.headers(self.reader), json=payload).status_code, 403)
        pay(self, self.reader, "a-book")
        created = self.client.post(review_path, headers=self.headers(self.reader), json=payload)
        self.assertEqual(created.status_code, 201)
        review_id = created.json["review"]["review_id"]
        path = f"{review_path}/{review_id}"
        self.assertEqual(created.json["review"]["created_by"], self.reader.user_id)
        self.assertEqual(created.json["review"]["description"], "A longer description")
        self.assertEqual(self.client.put(path, headers=self.headers(self.other), json={"comment": "Changed by another"}).status_code, 403)
        self.assertEqual(self.client.delete(path, headers=self.headers(self.other)).status_code, 403)
        self.assertEqual(self.client.put(path, headers=self.headers(self.reader), json={"comment": "Reader updated review"}).status_code, 200)
        self.assertEqual(self.client.put(path, headers=self.headers(self.admin), json={"description": "Admin moderation"}).status_code, 200)
        self.assertEqual(db.session.get(Review, review_id).updated_by, self.admin.user_id)
        self.assertEqual(self.client.delete(path, headers=self.headers(self.admin)).status_code, 200)
        self.assertTrue(db.session.get(Review, review_id).is_deleted)
        self.assertEqual(self.client.get(review_path).json["pagination"]["total"], 0)

    def test_one_active_review_per_purchaser(self):
        path = "/api/book/a-book/review"
        pay(self, self.reader, "a-book")
        payload = {"rating": 5, "comment": "A really useful book"}
        self.assertEqual(self.client.post(path, headers=self.headers(self.reader), json=payload).status_code, 201)
        self.assertEqual(self.client.post(path, headers=self.headers(self.reader), json=payload).status_code, 409)
        self.assertEqual(self.client.get("/api/book/a-book").json["average_rating"], 5)
        first = Review.query.one()
        self.client.delete(f"{path}/{first.review_id}", headers=self.headers(self.reader))
        self.assertEqual(self.client.post(path, headers=self.headers(self.reader), json=payload).status_code, 201)
        self.assertEqual(Review.query.count(), 2)

    def test_only_admin_edits_book_and_catalog_profiles(self):
        path = "/api/book/a-book"
        self.assertEqual(self.client.put(path, headers=self.headers(self.reader), json={"title": "New"}).status_code, 403)
        self.assertEqual(self.client.put(path, headers=self.headers(self.admin), json={"title": "New", "author": "New Writer"}).status_code, 200)
        self.assertIsNotNone(Author.query.filter_by(name="New Writer").first())
        db.session.add(Country(code="BH", name="Bahrain"))
        db.session.commit()
        response = self.client.post("/api/authors", headers=self.headers(self.admin),
                                    json={"name": "Another Writer", "description": "Writes library books", "country_code": "BH"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["author"]["country"]["code"], "BH")
        self.assertEqual(self.client.delete(path, headers=self.headers(self.admin)).status_code, 200)
        self.assertTrue(db.session.get(Book, self.book.book_id).is_deleted)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_country_sync_maps_provider_records(self):
        payload = b'[{"name":"Bahrain","alpha2Code":"BH","flags":{"svg":"https://example.test/bh.svg"}}]'
        with patch("services.country_service.urlopen", return_value=BytesIO(payload)):
            response = self.client.post("/api/countries/sync", headers=self.headers(self.admin))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["count"], 1)
        self.assertEqual(db.session.get(Country, "BH").flag_url, "https://example.test/bh.svg")

    def test_registration_uses_client_role_and_employee_cannot_edit_books(self):
        registered = self.client.post("/api/register", json={
            "user_name": "newclient", "email": "newclient@example.test",
            "password": "library123", "role": AccountRole.ADMIN.value,
        })
        self.assertEqual(registered.status_code, 201)
        self.assertEqual(User.query.filter_by(user_name="newclient").one().role, AccountRole.CLIENT.value)
        self.other.role = AccountRole.EMPLOYEE.value
        db.session.commit()
        response = self.client.put("/api/book/a-book", headers=self.headers(self.other), json={"title": "Changed"})
        self.assertEqual(response.status_code, 403)

    def test_admin_can_assign_group_permissions_and_expressions(self):
        admin_headers = self.headers(self.admin)
        self.assertEqual(self.client.get("/api/access/roles", headers=self.headers(self.reader)).status_code, 403)
        permission = self.client.post("/api/access/permissions", headers=admin_headers,
                                      json={"key": Permission.BOOK_EDIT_ANY.value, "label": "Edit books"})
        self.assertEqual(permission.status_code, 201)
        access_permission = self.client.post("/api/access/permissions", headers=admin_headers,
                                             json={"key": Permission.ACCESS_READ_ANY.value, "label": "Read access"})
        self.assertEqual(access_permission.status_code, 201)
        role = self.client.post("/api/access/roles", headers=admin_headers,
                                json={"key": "catalog-editor", "name": "Catalog editor",
                                      "permission_keys": [Permission.BOOK_EDIT_ANY.value, Permission.ACCESS_READ_ANY.value]})
        self.assertEqual(role.status_code, 201)
        group = self.client.post("/api/access/groups", headers=admin_headers,
                                 json={"name": "Editors", "role_keys": ["catalog-editor"]})
        self.assertEqual(group.status_code, 201)
        assignment = self.client.put(f"/api/access/users/{self.other.user_id}", headers=admin_headers,
                                     json={"role": AccountRole.EMPLOYEE.value, "access_role_keys": [],
                                           "group_ids": [group.json["group"]["group_id"]]})
        self.assertEqual(assignment.status_code, 200)
        self.assertTrue(has_access(self.other, any_of(Permission.BOOK_EDIT_ANY, owns(-1))))
        self.assertFalse(has_access(self.other, all_of(Permission.BOOK_EDIT_ANY, owns(-1))))
        self.assertEqual(self.client.put("/api/book/a-book", headers=self.headers(self.other),
                                         json={"title": "Edited by group"}).status_code, 403)
        self.assertEqual(self.client.get("/api/access/roles", headers=self.headers(self.other)).status_code, 403)
        self.assertEqual(self.client.put(f"/api/access/users/{self.admin.user_id}", headers=admin_headers,
                                         json={"role": AccountRole.CLIENT.value, "access_role_keys": [],
                                               "group_ids": []}).status_code, 403)

    def test_delegated_permissions_cannot_bypass_admin_or_review_ownership(self):
        admin_headers = self.headers(self.admin)
        permissions = [Permission.BOOK_WRITE_ONE, Permission.BOOK_EDIT_ANY,
                       Permission.BOOK_DELETE_ANY, Permission.BOOK_IMPORT,
                       Permission.BOOK_BULK_EDIT, Permission.BOOK_MEDIA_WRITE,
                       Permission.REVIEW_EDIT_ANY, Permission.REVIEW_DELETE_ANY]
        for permission in permissions:
            response = self.client.post("/api/access/permissions", headers=admin_headers,
                                        json={"key": permission.value, "label": permission.value})
            self.assertEqual(response.status_code, 201)
        role = self.client.post("/api/access/roles", headers=admin_headers,
                                json={"key": "delegated-writer", "name": "Delegated writer",
                                      "permission_keys": [item.value for item in permissions]})
        self.assertEqual(role.status_code, 201)
        assigned = self.client.put(f"/api/access/users/{self.other.user_id}", headers=admin_headers,
                                   json={"role": AccountRole.EMPLOYEE.value,
                                         "access_role_keys": ["delegated-writer"], "group_ids": []})
        self.assertEqual(assigned.status_code, 200)
        headers = self.headers(self.other)
        for method, path in [("post", "/api/book"), ("put", "/api/book/a-book"),
                             ("delete", "/api/book/a-book"), ("post", "/api/book/import"),
                             ("post", "/api/book/bulk"), ("post", f"/api/media/books/{self.book.book_id}")]:
            with self.subTest(path=path, method=method):
                self.assertEqual(getattr(self.client, method)(path, headers=headers, json={}).status_code, 403)
        pay(self, self.reader, "a-book")
        review = self.client.post("/api/book/a-book/review", headers=self.headers(self.reader),
                                  json={"rating": 4, "comment": "A thoughtful reader review"})
        self.assertEqual(review.status_code, 201)
        path = f"/api/book/a-book/review/{review.json['review']['review_id']}"
        self.assertEqual(self.client.put(path, headers=headers, json={"rating": 1}).status_code, 403)
        self.assertEqual(self.client.delete(path, headers=headers).status_code, 403)
        self.assertEqual(self.client.put(path, headers=admin_headers, json={"rating": 5}).status_code, 200)
        self.assertEqual(self.client.delete(path, headers=self.headers(self.reader)).status_code, 200)

    def test_book_socket_room_receives_review_change(self):
        socket_client = socketio.test_client(app)
        socket_client.emit("join_book", {"slug": "a-book"})
        pay(self, self.reader, "a-book")
        self.client.post("/api/book/a-book/review", headers=self.headers(self.reader),
                         json={"rating": 4, "comment": "A good live review"})
        events = socket_client.get_received()
        self.assertTrue(any(event["name"] == "book_changed" and event["args"][0]["resource"] == "reviews" for event in events))
        socket_client.disconnect()

    def test_rental_has_fee_term_and_return_workflow(self):
        pay(self, self.reader, "a-book", "rental")
        rented = self.client.get("/api/book/a-book/loan", headers=self.headers(self.reader))
        self.assertEqual(rented.status_code, 200)
        self.assertEqual(rented.json["loan"]["loan_kind"], "rent")
        self.assertEqual(rented.json["loan"]["rental_fee"], 1.0)
        self.assertEqual(self.client.post("/api/book/a-book/borrow", headers=self.headers(self.reader)).status_code, 409)
        returned = self.client.post("/api/book/a-book/return", headers=self.headers(self.reader))
        self.assertEqual(returned.json["loan"]["status"], "returned")

    def test_inventory_export_import_and_bulk_soft_delete(self):
        admin_headers = self.headers(self.admin)
        self.assertEqual(self.client.get("/api/book/export?format=xlsx", headers=admin_headers).status_code, 200)
        pdf = self.client.get("/api/book/export?format=pdf", headers=admin_headers)
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.data.startswith(b"%PDF"))
        payload = b"title,isbn,author,publisher,published_at,price,copies_total,condition\nImported Book,999,Writer,Press,2020-01-01,3.5,2,good\n"
        imported = self.client.post("/api/book/import", headers=admin_headers,
                                    data={"file": (BytesIO(payload), "books.csv")}, content_type="multipart/form-data")
        self.assertEqual(imported.status_code, 201)
        imported_id = imported.json["book_ids"][0]
        self.assertEqual(self.client.post("/api/book/bulk", headers=admin_headers,
                                          json={"ids": [imported_id], "action": "archive"}).status_code, 200)
        self.assertEqual(self.client.get("/api/?q=Imported").json["pagination"]["total"], 0)
        self.assertEqual(self.client.get("/api/book/manage?q=Imported", headers=admin_headers).json["pagination"]["total"], 1)
        self.assertEqual(self.client.post("/api/book/bulk", headers=admin_headers,
                                          json={"ids": [imported_id], "action": "delete"}).status_code, 200)
        self.assertTrue(db.session.get(Book, imported_id).is_deleted)


if __name__ == "__main__":
    unittest.main()
