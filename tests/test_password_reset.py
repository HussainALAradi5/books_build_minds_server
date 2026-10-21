"""Account identifier and password reset contract checks."""
import os
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from werkzeug.security import generate_password_hash

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-long-enough-for-hs256"

from app import app, limiter  # noqa: E402
from config import db  # noqa: E402
from models.accounts.PasswordResetCode import PasswordResetCode  # noqa: E402
from models.accounts.User import User  # noqa: E402
from services.accounts.reset_delivery import send_reset_code  # noqa: E402
from utils.accounts.security import create_token  # noqa: E402


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        limiter.enabled = False
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        self.user = User(user_name="reader", email="reader@example.test", mobile_number="+97312345678",
                         password_digest=generate_password_hash("Oldpass123"), is_active=True)
        db.session.add(self.user)
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_username_email_and_mobile_login_require_password(self):
        for identifier in ("reader", "reader@example.test", "+97312345678"):
            response = self.client.post("/api/login", json={"identifier": identifier, "password": "Oldpass123"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["user_id"], self.user.user_id)
        self.assertEqual(self.client.post("/api/login", json={"identifier": "+97312345678"}).status_code, 401)

    def test_registration_validates_unique_international_mobile(self):
        duplicate = self.client.post("/api/register", json={"user_name": "someone", "email": "new@example.test",
                                                               "mobile_number": "+97312345678", "password": "Safepass123"})
        self.assertEqual(duplicate.status_code, 409)
        invalid = self.client.post("/api/register", json={"user_name": "someone", "email": "new@example.test",
                                                             "mobile_number": "12345", "password": "Safepass123"})
        self.assertEqual(invalid.status_code, 400)

    def test_owner_can_set_mobile_and_use_it_to_sign_in(self):
        response = self.client.put(f"/api/profile/{self.user.user_id}/edit",
                                   headers={"Authorization": f"Bearer {create_token(self.user)}"},
                                   json={"mobile_number": "+973 3333 4444"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["user"]["mobile_number"], "+97333334444")
        self.assertEqual(self.client.post("/api/login", json={
            "identifier": "+97333334444", "password": "Oldpass123"}).status_code, 200)

    def test_reset_code_is_single_use_and_revokes_old_tokens(self):
        sent = []
        with patch("services.accounts.password_reset_service.delivery_ready", return_value=True), \
             patch("services.accounts.password_reset_service.send_reset_code", side_effect=lambda email, code: sent.append((email, code))):
            response = self.client.post("/api/password-reset/request", json={"identifier": "+97312345678"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sent[0][0], "reader@example.test")
        self.assertNotIn(sent[0][1], str(response.json))
        old_version = self.user.token_version
        confirm = {"identifier": "reader", "code": sent[0][1], "new_password": "Newpass123"}
        self.assertEqual(self.client.post("/api/password-reset/confirm", json=confirm).status_code, 200)
        self.assertEqual(self.user.token_version, old_version + 1)
        self.assertEqual(self.client.post("/api/password-reset/confirm", json=confirm).status_code, 400)
        self.assertEqual(self.client.post("/api/password-reset/confirm", json={
            **confirm, "code": f"{sent[0][1]}0"}).status_code, 400)
        self.assertEqual(self.client.post("/api/login", json={"identifier": "reader", "password": "Oldpass123"}).status_code, 401)
        self.assertEqual(self.client.post("/api/login", json={"identifier": "reader", "password": "Newpass123"}).status_code, 200)

    def test_request_does_not_reveal_unknown_account_and_wrong_codes_lock(self):
        sent = []
        with patch("services.accounts.password_reset_service.delivery_ready", return_value=True), \
             patch("services.accounts.password_reset_service.send_reset_code", side_effect=lambda email, code: sent.append(code)):
            unknown = self.client.post("/api/password-reset/request", json={"identifier": "unknown@example.test"})
            known = self.client.post("/api/password-reset/request", json={"identifier": "reader"})
        self.assertEqual(unknown.json, known.json)
        self.assertEqual(len(sent), 1)
        for _ in range(5):
            self.assertEqual(self.client.post("/api/password-reset/confirm", json={
                "identifier": "reader", "code": "000000" if sent[0] != "000000" else "111111",
                "new_password": "Newpass123"}).status_code, 400)
        self.assertEqual(self.client.post("/api/password-reset/confirm", json={
            "identifier": "reader", "code": sent[0], "new_password": "Newpass123"}).status_code, 400)

    def test_expired_code_and_missing_delivery(self):
        with patch("services.accounts.password_reset_service.delivery_ready", return_value=False):
            self.assertEqual(self.client.post("/api/password-reset/request", json={"identifier": "reader"}).status_code, 503)
        with patch("services.accounts.password_reset_service.delivery_ready", return_value=True), \
             patch("services.accounts.password_reset_service.send_reset_code") as sender:
            self.assertEqual(self.client.post("/api/password-reset/request", json={"identifier": "reader"}).status_code, 200)
        code = sender.call_args.args[1]
        item = PasswordResetCode.query.first()
        item.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()
        self.assertEqual(self.client.post("/api/password-reset/confirm", json={
            "identifier": "reader", "code": code, "new_password": "Newpass123"}).status_code, 400)

    def test_resend_adapter_keeps_credentials_on_server(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        with patch.dict(os.environ, {"PASSWORD_RESET_DELIVERY": "", "RESEND_API_KEY": "re_test_secret",
                                          "RESEND_FROM_EMAIL": "Library <reset@example.test>"}), \
             patch("services.accounts.reset_delivery.urlopen", return_value=Response()) as upstream:
            send_reset_code("reader@example.test", "123456")
        request = upstream.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(request.get_header("Authorization"), "Bearer re_test_secret")
        self.assertEqual(json.loads(request.data)["to"], ["reader@example.test"])


if __name__ == "__main__":
    unittest.main()
