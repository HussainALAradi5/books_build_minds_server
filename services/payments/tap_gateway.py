"""Tap hosted BHD sandbox. Card data never enters this application."""
import hashlib
import hmac
import json
import re
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from flask import current_app
from utils.payments.errors import PaymentError
from utils.printing.book_codes import book_url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def client():
    key = current_app.config.get("TAP_SECRET_KEY", "")
    if not key.startswith("sk_test_"):
        raise PaymentError("Tap sandbox checkout is not configured", 503)
    return key


def request_api(path, payload=None):
    request = Request("https://api.tap.company/v2/" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": "Bearer " + client(), "Content-Type": "application/json"})
    try:
        with build_opener(NoRedirect).open(request, timeout=20) as response:
            result = json.loads(response.read(1_000_001))
        if not isinstance(result, dict):
            raise ValueError("Invalid provider response")
        return result
    except (HTTPError, URLError, TimeoutError, ValueError):
        # Ambiguous failures retain the reservation and the same idempotency key.
        raise PaymentError("Tap unavailable or rejected the request. Retry from Transactions; stock remains reserved.", 502) from None


def webhook_url():
    url = current_app.config.get("TAP_WEBHOOK_URL", "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise PaymentError("Configure a public HTTPS Tap webhook URL", 503)
    return url


def provider_id(value, prefix):
    if not isinstance(value, str) or not re.fullmatch(prefix + r"[A-Za-z0-9_-]+", value):
        raise PaymentError("Invalid payment provider reference", 400)
    return value


def normalize(charge):
    if charge.get("object") != "charge" or charge.get("live_mode") is not False:
        raise PaymentError("Only sandbox charges are accepted", 409)
    identifier = provider_id(charge.get("id"), "chg_")
    amount = Decimal(str(charge.get("amount"))) * 1000
    if not amount.is_finite() or amount != amount.to_integral_value() or amount <= 0:
        raise PaymentError("Invalid provider amount", 409)
    state = charge.get("status")
    ended = state in {"ABANDONED", "CANCELLED", "FAILED", "DECLINED", "RESTRICTED", "VOID", "TIMEDOUT"}
    return {"id": identifier, "client_reference_id": charge.get("reference", {}).get("transaction"),
        "metadata": charge.get("metadata", {}), "currency": str(charge.get("currency", "")).lower(),
        "amount_total": int(amount), "mode": "payment", "livemode": False,
        "payment_status": "paid" if state == "CAPTURED" else "unpaid",
        "payment_reference": identifier if state == "CAPTURED" else None,
        "status": "expired" if ended else "open", "url": charge.get("transaction", {}).get("url")}


def create_session(transaction):
    charge = request_api("charges/", {
        "amount": transaction.amount_minor / transaction.currency_scale, "currency": "BHD",
        "customer_initiated": True, "threeDSecure": True, "save_card": False,
        "description": f"{transaction.kind.title()}: {transaction.book_title}",
        "metadata": {"transaction_id": transaction.transaction_id},
        "reference": {"transaction": transaction.transaction_id, "order": transaction.transaction_id,
                      "idempotent": f"checkout-{transaction.transaction_id}"},
        "customer": {"first_name": transaction.customer_name}, "source": {"id": "src_all"},
        "transaction": {"expiry": {"period": 35, "type": "MINUTE"}},
        "post": {"url": webhook_url()},
        "redirect": {"url": f"{book_url(transaction.book_slug)}?transaction={transaction.transaction_id}"}})
    return normalize(charge)


def retrieve_session(charge_id):
    return normalize(request_api("charges/" + provider_id(charge_id, "chg_")))


def refund(transaction):
    if transaction.provider_refund_id:
        return request_api("refunds/" + provider_id(transaction.provider_refund_id, "re_"))
    return request_api("refunds/", {"charge_id": transaction.provider_payment_id,
        "amount": transaction.amount_minor / transaction.currency_scale, "currency": "BHD",
        "reason": "requested_by_customer", "metadata": {"transaction_id": transaction.transaction_id},
        "reference": {"idempotent": f"refund-{transaction.transaction_id}"}})


def verify_event(payload, signature):
    charge = json.loads(payload)
    if not isinstance(charge, dict) or charge.get("object") != "charge":
        raise ValueError("Expected charge")
    reference = charge.get("reference", {})
    message = (f"x_id{charge['id']}x_amount{Decimal(str(charge['amount'])):.3f}"
        f"x_currency{charge['currency']}x_gateway_reference{reference.get('gateway', '')}"
        f"x_payment_reference{reference.get('payment', '')}x_status{charge['status']}"
        f"x_created{charge['transaction']['created']}")
    expected = hmac.new(client().encode(), message.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Invalid signature")
    normalize(charge)
    return charge
