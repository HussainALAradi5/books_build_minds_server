from flask import Blueprint, jsonify, request
from config import db
from enums.accounts.permission import Permission
from services.payments import tap_gateway, transaction_service
from services.payments.checkout_service import start_checkout
from services.payments.fulfillment_service import apply_session
from services.receipts.receipt_service import download_transaction_receipt
from utils.accounts.security import require_user
from utils.payments.errors import PaymentError
from utils.shared.responses import error
from utils.shared.validation import json_body

payments = Blueprint("payments", __name__)

@payments.errorhandler(PaymentError)
def payment_error(exc):
    db.session.rollback()
    return error(str(exc), exc.status)

@payments.errorhandler(ValueError)
def invalid_input(_exc):
    db.session.rollback()
    return error("Invalid payment request", 400)

@payments.post("/transactions/checkout")
@require_user()
def checkout():
    from flask import g
    from utils.access.access import has_access
    data = json_body()
    permission = Permission.LOAN_WRITE_ONE if data.get("kind") == "rental" else Permission.PURCHASE_WRITE_ONE
    if not has_access(g.user, permission):
        return error("Access denied", 403)
    return jsonify(start_checkout(data).to_dict())

@payments.get("/transactions")
@require_user()
def listing():
    return jsonify(transaction_service.list_transactions())

@payments.get("/transactions/<string:transaction_id>")
@require_user()
def detail(transaction_id):
    return jsonify(transaction_service.owned_transaction(transaction_id).to_dict())

@payments.post("/transactions/<string:transaction_id>/sync")
@require_user()
def sync(transaction_id):
    return jsonify(transaction_service.reconcile(transaction_service.owned_transaction(transaction_id)).to_dict())

@payments.post("/transactions/<string:transaction_id>/cancel")
@require_user()
def cancel(transaction_id):
    return jsonify(transaction_service.cancel(transaction_service.owned_transaction(transaction_id)).to_dict())

@payments.get("/transactions/<string:transaction_id>/receipt")
@require_user()
def receipt(transaction_id):
    return download_transaction_receipt(transaction_service.owned_transaction(transaction_id))

@payments.post("/payments/tap/webhook")
def webhook():
    if request.content_length is None or request.content_length > 65536:
        return error("Invalid webhook size", 413)
    try:
        charge = tap_gateway.verify_event(request.get_data(), request.headers.get("hashstring", ""))
    except (ValueError, KeyError, TypeError, ArithmeticError):
        return error("Invalid webhook signature or payload", 400)
    # Always retrieve canonical state; signed payloads can be replayed or delivered out of order.
    session = tap_gateway.retrieve_session(charge["id"])
    import hashlib
    event_id = hashlib.sha256(f"{charge['id']}:{session['status']}:{session['payment_status']}".encode()).hexdigest()
    apply_session(session, event_id, "charge.updated")
    return jsonify({"received": True})
