import unittest
from types import SimpleNamespace
from unittest.mock import patch
from config import app
from services.payments import tap_gateway
from utils.payments.errors import PaymentError


class TapGatewayTests(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context()
        self.context.push()
        self.charge = {"id": "chg_test_fixture", "object": "charge", "live_mode": False,
            "amount": 5.125, "currency": "BHD", "status": "CAPTURED",
            "reference": {"transaction": "fixture"}, "metadata": {"transaction_id": "fixture"},
            "transaction": {"url": "https://sandbox.payments.tap.company/test"}}

    def tearDown(self):
        self.context.pop()

    def test_fils_and_terminal_states(self):
        self.assertEqual(tap_gateway.normalize(self.charge)["amount_total"], 5125)
        self.assertEqual(tap_gateway.normalize(self.charge)["payment_status"], "paid")
        for state in ["ABANDONED", "CANCELLED", "FAILED", "DECLINED", "RESTRICTED", "VOID", "TIMEDOUT"]:
            value = tap_gateway.normalize({**self.charge, "status": state})
            self.assertEqual(value["status"], "expired")
            self.assertEqual(value["payment_status"], "unpaid")
        self.assertEqual(tap_gateway.normalize({**self.charge, "status": "UNKNOWN"})["status"], "open")

    def test_live_keys_live_charges_and_unsafe_identifiers_rejected(self):
        with patch.dict(app.config, TAP_SECRET_KEY="sk_live_forbidden"):
            with self.assertRaises(PaymentError): tap_gateway.client()
        with self.assertRaises(PaymentError): tap_gateway.normalize({**self.charge, "live_mode": True})
        with self.assertRaises(PaymentError): tap_gateway.retrieve_session("../refunds")

    def test_checkout_uses_fixed_bhd_amount_and_same_idempotency_key(self):
        item = SimpleNamespace(amount_minor=5125, currency_scale=1000, kind="purchase",
            book_title="Test", transaction_id="fixture", customer_name="Reader", book_slug="test")
        with patch.dict(app.config, TAP_WEBHOOK_URL="https://library.example/api/payments/tap/webhook"), \
             patch.object(tap_gateway, "request_api", return_value=self.charge) as request:
            tap_gateway.create_session(item)
            first = request.call_args.args[1]
            tap_gateway.create_session(item)
            self.assertEqual(first, request.call_args.args[1])
            self.assertEqual(first["reference"]["idempotent"], "checkout-fixture")
            self.assertEqual((first["amount"], first["currency"]), (5.125, "BHD"))
            self.assertEqual(first["source"]["id"], "src_all")

    def test_refund_retrieves_existing_request_instead_of_creating_again(self):
        item = SimpleNamespace(provider_refund_id="re_test_fixture")
        with patch.object(tap_gateway, "request_api", return_value={}) as request:
            tap_gateway.refund(item)
            request.assert_called_once_with("refunds/re_test_fixture")
