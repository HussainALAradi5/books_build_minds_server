import os
import hashlib
import hmac
import json
import time
import unittest
from datetime import date
from uuid import uuid4
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-long-enough-for-hs256"
from app import app, limiter
from config import db
from models.accounts.User import User
from models.catalog.Book import Book
from models.library.Loan import Loan
from models.payments.Transaction import Transaction
from models.payments.PaymentEvent import PaymentEvent
from models.receipts.Receipt import Receipt
from constants.library_policy import POLICY_VERSION
from utils.accounts.security import create_token
from services.payments.fulfillment_service import apply_session
from payment_fixture import checkout, pay, provider_session

class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context(); self.context.push()
        limiter.enabled = False
        db.create_all()
        self.user = User(user_name="payer", email="payer@example.test", password_digest="hash")
        self.other = User(user_name="other-payer", email="other@example.test", password_digest="hash")
        self.admin = User(user_name="cashier", email="cashier@example.test", password_digest="hash", is_admin=True)
        db.session.add_all([self.user, self.other, self.admin]); db.session.flush()
        self.book = Book(title="Payment book", slug="payment-book", isbn="payment-isbn", author="Author", publisher="Press",
                         price=5, copies_total=1, published_at=date(2020,1,1), added_by_user_id=self.admin.user_id)
        db.session.add(self.book); db.session.commit()
        self.client = app.test_client()
        self.terms = {"accepted_terms": True, "policy_version": POLICY_VERSION}

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.context.pop()

    def headers(self, user=None):
        return {"Authorization": f"Bearer {create_token(user or self.user)}"}

    def test_no_keys_no_checkout_and_no_unpaid_shortcut(self):
        with patch.dict(app.config, TAP_SECRET_KEY=""):
            response = self.client.post("/api/transactions/checkout", json={}, headers=self.headers())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(Transaction.query.count(), 0)
        for action in ("purchase", "rent"):
            self.assertEqual(self.client.post(f"/api/book/payment-book/{action}", headers=self.headers()).status_code, 409)
        self.assertEqual(len(self.user.purchased_books), 0)

    def test_pending_stock_and_duplicate_checkout(self):
        first = checkout(self, self.user, self.book.slug)
        second = checkout(self, self.user, self.book.slug)
        self.assertEqual(first.json["transaction_id"], second.json["transaction_id"])
        self.assertEqual(Transaction.query.count(), 1)
        self.assertEqual(self.client.post("/api/book/payment-book/borrow", json=self.terms, headers=self.headers(self.other)).status_code, 409)
        self.assertEqual(checkout(self, self.other, self.book.slug).status_code, 409)
        self.assertEqual(self.client.post("/api/book/bulk", json={"ids":[self.book.book_id], "action":"archive"}, headers=self.headers(self.admin)).status_code,409)

    def test_verified_payment_once_and_receipt_snapshot(self):
        item = pay(self, self.user, self.book.slug)
        apply_session(provider_session(item), "evt_duplicate_1", "checkout.session.completed")
        apply_session(provider_session(item), "evt_duplicate_1", "checkout.session.completed")
        self.assertEqual(Receipt.query.count(), 1)
        self.assertEqual(PaymentEvent.query.count(), 1)
        self.assertEqual(len(self.user.purchased_books), 1)
        self.assertEqual(self.book.available_copies, 0)
        self.book.price=99; self.book.title="Changed later"; db.session.commit()
        receipt=Receipt.query.one()
        self.assertEqual(receipt.amount_minor, 5000)
        self.assertEqual(receipt.book_title, "Payment book")
        response=self.client.get(f"/api/transactions/{item.transaction_id}/receipt",headers=self.headers())
        self.assertEqual(response.status_code,200); self.assertTrue(response.data.startswith(b"%PDF-"))
        self.assertEqual(self.client.get(f"/api/transactions/{item.transaction_id}/receipt",headers=self.headers(self.other)).status_code,404)

    def test_expired_checkout_releases_stock_without_payment(self):
        response=checkout(self,self.user,self.book.slug)
        item=db.session.get(Transaction,response.json["transaction_id"])
        apply_session(provider_session(item,False,"expired"))
        self.assertEqual(item.status,"expired")
        self.assertEqual(self.book.available_copies,1)
        self.assertEqual(Receipt.query.count(),0)
        self.assertEqual(self.client.get(f"/api/transactions/{item.transaction_id}/receipt",headers=self.headers()).status_code,409)

    def test_rental_payment_and_repeated_rental_receipts(self):
        first=pay(self,self.user,self.book.slug,"rental")
        loan=Loan.query.one()
        self.assertEqual((loan.due_at-loan.borrowed_at).days,7)
        self.assertEqual(first.amount_minor,1000)
        self.assertEqual(self.client.post("/api/book/payment-book/return",headers=self.headers()).status_code,200)
        pay(self,self.user,self.book.slug,"rental")
        self.assertEqual(Receipt.query.count(),2)
        self.assertEqual(Loan.query.count(),2)

    def test_signature_verification_and_unpaid_event(self):
        response=checkout(self,self.user,self.book.slug)
        item=db.session.get(Transaction,response.json["transaction_id"])
        charge={"id":item.provider_charge_id, "object":"charge", "live_mode":False,
            "amount":5, "currency":"BHD", "reference":{"transaction":item.transaction_id},
            "status":"INITIATED", "transaction":{"created":"123"}}
        payload=json.dumps(charge).encode(); secret="sk_test_fixture"
        message=f"x_id{charge['id']}x_amount5.000x_currencyBHDx_gateway_referencex_payment_referencex_statusINITIATEDx_created123"
        signature=hmac.new(secret.encode(),message.encode(),hashlib.sha256).hexdigest()
        with patch.dict(app.config, TAP_SECRET_KEY=secret):
            self.assertEqual(self.client.post("/api/payments/tap/webhook",data=payload).status_code,400)
            with patch("services.payments.tap_gateway.retrieve_session",return_value=provider_session(item,False,"open")):
                result=self.client.post("/api/payments/tap/webhook",data=payload,headers={"hashstring":signature})
                self.assertEqual(result.status_code,200,result.json)
        self.assertEqual(item.status,"pending");self.assertEqual(Receipt.query.count(),0)

    def test_wrong_amount_or_mode_cannot_fulfill(self):
        response=checkout(self,self.user,self.book.slug); item=db.session.get(Transaction,response.json["transaction_id"])
        for field,value in [("amount_total",1),("currency","usd"),("livemode",True),("client_reference_id","missing")]:
            session=provider_session(item); session[field]=value
            with self.assertRaises(Exception): apply_session(session)
            db.session.rollback()
        self.assertEqual(Receipt.query.count(),0)
        self.assertEqual(len(self.user.purchased_books),0)

    def test_quote_terms_hidden_records_and_price_change(self):
        self.assertEqual(self.client.post("/api/book/payment-book/borrow",headers=self.headers()).status_code,409)
        self.book.is_archived=True;db.session.commit()
        self.assertEqual(self.client.post("/api/book/payment-book/borrow",json=self.terms,headers=self.headers()).status_code,404)
        self.book.is_archived=False;db.session.commit()
        with patch("services.payments.tap_gateway.client"), patch("services.payments.tap_gateway.webhook_url"):
            result=self.client.post("/api/transactions/checkout",headers=self.headers(),json={**self.terms,
              "book_slug":self.book.slug,"kind":"purchase","request_key":str(uuid4()),"expected_amount_minor":1})
        self.assertEqual(result.status_code,409)
        self.assertEqual(Transaction.query.count(),0)

    def test_logout_revokes_existing_token(self):
        headers=self.headers()
        self.assertEqual(self.client.post("/api/logout",headers=headers).status_code,200)
        self.assertEqual(self.client.get("/api/transactions",headers=headers).status_code,401)

    def test_disabled_account_payment_requires_refund(self):
        response=checkout(self,self.user,self.book.slug);item=db.session.get(Transaction,response.json["transaction_id"])
        self.user.is_active=False;db.session.commit()
        apply_session(provider_session(item))
        self.assertEqual(item.status,"refund_pending")
        self.assertEqual(len(self.user.purchased_books),0)
        self.assertEqual(Receipt.query.count(),0)

    def test_old_expiration_event_does_not_undo_completed_payment(self):
        item=pay(self,self.user,self.book.slug)
        apply_session(provider_session(item), "evt_old_expired", "checkout.session.expired")
        self.assertEqual(item.status,"completed")
        self.assertEqual(Receipt.query.count(),1)

    def test_refund_pending_then_confirmed_without_fulfillment(self):
        from services.payments.fulfillment_service import retry_refund
        response=checkout(self,self.user,self.book.slug)
        item=db.session.get(Transaction,response.json["transaction_id"])
        self.user.is_active=False;db.session.commit()
        apply_session(provider_session(item))
        refund={"id":"re_test_refund", "charge_id":item.provider_payment_id,
                "amount":5, "currency":"BHD", "live_mode":False, "status":"PENDING"}
        with patch("services.payments.tap_gateway.refund",return_value=refund):
            retry_refund(item)
        self.assertEqual(item.provider_refund_id,"re_test_refund")
        self.assertEqual(item.status,"refund_pending")
        with patch("services.payments.tap_gateway.refund",return_value={**refund,"status":"REFUNDED"}):
            retry_refund(item)
        self.assertEqual(item.status,"refunded")
        self.assertEqual(Receipt.query.count(),0)

    def test_active_cancel_does_not_release_reservation(self):
        response=checkout(self,self.user,self.book.slug)
        item=db.session.get(Transaction,response.json["transaction_id"])
        with patch("services.payments.tap_gateway.retrieve_session",return_value=provider_session(item,False)):
            result=self.client.post(f"/api/transactions/{item.transaction_id}/cancel",headers=self.headers())
        self.assertEqual(result.status_code,409)
        self.assertEqual(item.status,"pending")
        self.assertEqual(self.book.available_copies,0)
