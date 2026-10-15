"""A fake provider used only by tests; no runtime payment bypass exists."""
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch
from flask import g
from config import app, db
from constants.library_policy import POLICY_VERSION
from models.Book import Book
from models.payments.Transaction import Transaction
from services.payments.fulfillment_service import apply_session
from utils.security import create_token
from utils.payments.money import price_minor

def provider_session(item, paid=True, status=None):
    return {"id": f"chg_test_{item.transaction_id}", "client_reference_id": item.transaction_id,
            "metadata": {"transaction_id": item.transaction_id}, "currency": item.currency,
            "amount_total": item.amount_minor, "mode": "payment", "livemode": False,
            "payment_status": "paid" if paid else "unpaid", "status": status or ("complete" if paid else "open"),
            "payment_reference": f"chg_test_{item.transaction_id}" if paid else None}

def checkout(test, user, slug, kind="purchase", request_key=None):
    book = Book.query.filter_by(slug=slug).one()
    data = {"book_slug": slug, "kind": kind, "request_key": request_key or str(uuid4()),
            "accepted_terms": True, "policy_version": POLICY_VERSION,
            "expected_amount_minor": price_minor(book.price, kind == "rental")}
    def create(item):
        return {**provider_session(item, False), "url": "https://sandbox.payments.tap.company/test"}
    with patch("services.payments.tap_gateway.client"), patch("services.payments.tap_gateway.webhook_url"), patch("services.payments.tap_gateway.create_session", side_effect=create):
        response = test.client.post("/api/transactions/checkout", json=data,
            headers={"Authorization": f"Bearer {create_token(user)}"})
    return response

def pay(test, user, slug, kind="purchase"):
    response = checkout(test, user, slug, kind)
    test.assertEqual(response.status_code, 200, response.json)
    item = db.session.get(Transaction, response.json["transaction_id"])
    apply_session(provider_session(item))
    return item
