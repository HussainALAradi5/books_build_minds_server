"""Owner-scoped transactions and authenticated recovery operations."""
from flask import g, request
from config import db
from enums.payments.transaction_status import TransactionStatus
from models.payments.Transaction import Transaction
from services.payments import tap_gateway
from services.payments.checkout_service import ensure_checkout
from services.payments.fulfillment_service import apply_session, retry_refund
from utils.pagination import page_options, paginate, order_query
from utils.payments.errors import PaymentError

def owned_transaction(transaction_id):
    item = db.session.get(Transaction, transaction_id)
    if not item or item.is_deleted or item.is_archived:
        raise PaymentError("Transaction not found", 404)
    if item.user_id != g.user.user_id and not g.user.is_admin:
        raise PaymentError("Transaction not found", 404)
    return item

def list_transactions():
    options = page_options()
    query = Transaction.query.filter_by(user_id=g.user.user_id, is_deleted=False, is_archived=False)
    status = request.args.get("status")
    if status:
        if status not in {item.value for item in TransactionStatus}:
            raise PaymentError("Unsupported transaction status")
        query = query.filter_by(status=status)
    return paginate(order_query(query, Transaction.created_at, options, Transaction.transaction_id),
                    lambda item: item.to_dict(), options)

def reconcile(item):
    if item.status == TransactionStatus.REFUND_PENDING:
        return retry_refund(item)
    if item.status != TransactionStatus.PENDING:
        return item
    item = ensure_checkout(item)
    return apply_session(tap_gateway.retrieve_session(item.provider_charge_id))

def cancel(item):
    item = reconcile(item)
    if item.status != TransactionStatus.PENDING:
        return item
    raise PaymentError("Tap checkout is still active. Cancel on the hosted payment page or wait for provider expiration, then refresh. Stock remains reserved until confirmed.", 409)
