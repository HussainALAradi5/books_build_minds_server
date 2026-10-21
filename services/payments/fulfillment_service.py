"""Apply one verified payment and all its library changes atomically."""
from datetime import datetime, timedelta, timezone
from config import db
from constants.library_policy import RENTAL_DAYS
from enums.payments.transaction_kind import TransactionKind
from enums.payments.transaction_status import TransactionStatus
from models.library.LibraryActivity import LibraryActivity
from models.library.Loan import Loan
from models.payments.Transaction import Transaction
from models.payments.PaymentEvent import PaymentEvent
from models.receipts.Receipt import Receipt
from services.payments import tap_gateway
from utils.books.inventory import locked_book
from utils.payments.errors import PaymentError
from utils.books.book_events import emit_book_changed

def apply_session(session, event_id=None, event_type="reconcile"):
    reference = session.get("client_reference_id")
    item = db.session.get(Transaction, reference) if reference else None
    if not item:
        raise PaymentError("Unknown checkout transaction", 404)
    book = locked_book(item.book_id)
    item = Transaction.query.filter_by(transaction_id=reference).populate_existing().with_for_update().one()
    if event_id and db.session.get(PaymentEvent, event_id):
        db.session.commit()
        return item
    if (session.get("livemode") is not False or session.get("mode") != "payment"
        or session.get("currency") != item.currency or session.get("amount_total") != item.amount_minor
        or session.get("metadata", {}).get("transaction_id") != reference
        or (item.provider_charge_id and session.get("id") != item.provider_charge_id)):
        raise PaymentError("Payment verification mismatch", 409)
    item.provider_charge_id = session["id"]
    if event_id:
        db.session.add(PaymentEvent(event_id=event_id, transaction_id=reference, event_type=event_type))
    paid = session.get("payment_status") == "paid"
    if item.status == TransactionStatus.PENDING and paid:
        intent = session.get("payment_reference")
        if not isinstance(intent, str) or not intent:
            raise PaymentError("Paid checkout has no payment reference", 409)
        item.provider_payment_id = intent
        item.paid_at = datetime.now(timezone.utc)
        user = item.user
        if book.is_deleted or book.is_archived or not user.is_active or user.is_deleted or user.is_archived:
            item.status = TransactionStatus.REFUND_PENDING.value
            item.failure_reason = "Book or account unavailable; refund required"
        elif item.kind == TransactionKind.PURCHASE and book in user.purchased_books:
            item.status = TransactionStatus.REFUND_PENDING.value
            item.failure_reason = "Already owned; duplicate payment refund required"
        else:
            complete(item, book, user)
    elif paid and item.status in (TransactionStatus.EXPIRED, TransactionStatus.FAILED):
        item.provider_payment_id = session.get("payment_reference")
        item.status = TransactionStatus.REFUND_PENDING.value
        item.failure_reason = "Late payment after stock release; refund required"
    elif item.status == TransactionStatus.PENDING and session.get("status") == "expired":
        item.status = TransactionStatus.EXPIRED.value
    # Never roll back a completed transaction because an old event arrived later.
    db.session.commit()
    emit_book_changed(book.slug, "inventory")
    return item

def complete(item, book, user):
    now = datetime.now(timezone.utc)
    if item.kind == TransactionKind.PURCHASE:
        user.purchased_books.append(book)
        actions = [(user.user_id, "buy"), (book.added_by_user_id, "sell")]
    else:
        existing = Loan.query.filter_by(book_id=book.book_id, user_id=user.user_id,
                                       returned_at=None, is_deleted=False, is_archived=False).first()
        if existing:
            item.status = TransactionStatus.REFUND_PENDING.value
            item.failure_reason = "Active loan already exists; refund required"
            return
        db.session.add(Loan(user_id=user.user_id, book_id=book.book_id, borrowed_at=now,
            due_at=now + timedelta(days=RENTAL_DAYS), loan_kind="rent",
            rental_fee=item.amount_minor / item.currency_scale, transaction_id=item.transaction_id, policy_version=item.policy_version))
        actions = [(user.user_id, "rent")]
    item.status = TransactionStatus.COMPLETED.value
    for user_id, action in actions:
        db.session.add(LibraryActivity(user_id=user_id, book_id=book.book_id, action_type=action))
    db.session.add(Receipt(user_id=user.user_id, book_id=book.book_id, written_time=now.date(),
        transaction_id=item.transaction_id, amount_minor=item.amount_minor, currency=item.currency,
        currency_scale=item.currency_scale, book_title=item.book_title, book_author=item.book_author,
        customer_name=item.customer_name, kind=item.kind))

def retry_refund(item):
    if item.status != TransactionStatus.REFUND_PENDING:
        return item
    from decimal import Decimal
    now = datetime.now(timezone.utc)
    locked_book(item.book_id)
    item = Transaction.query.filter_by(transaction_id=item.transaction_id).populate_existing().with_for_update().one()
    if item.status != TransactionStatus.REFUND_PENDING:
        return item
    if not item.provider_refund_id:
        if item.refund_started_at and now - item.refund_started_at.replace(tzinfo=timezone.utc) >= timedelta(hours=23):
            raise PaymentError("Refund requires administrator reconciliation before retrying", 409)
        item.refund_started_at = item.refund_started_at or now
        db.session.commit()
    result = tap_gateway.refund(item)
    locked_book(item.book_id)
    item = Transaction.query.filter_by(transaction_id=item.transaction_id).populate_existing().with_for_update().one()
    if (result.get("charge_id") != item.provider_payment_id or result.get("currency") != item.currency.upper()
        or result.get("live_mode") is not False
        or Decimal(str(result.get("amount"))) * item.currency_scale != item.amount_minor):
        raise PaymentError("Refund verification mismatch", 409)
    refund_id = tap_gateway.provider_id(result.get("id"), "re_")
    if item.provider_refund_id and item.provider_refund_id != refund_id:
        raise PaymentError("Refund reference mismatch", 409)
    item.provider_refund_id = refund_id
    if result.get("status") == "REFUNDED":
        item.status = TransactionStatus.REFUNDED.value
    db.session.commit()
    return item
