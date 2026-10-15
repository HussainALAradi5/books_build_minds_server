"""Persist reservations before remote calls; retry the same provider request safely."""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from flask import g
from sqlalchemy.exc import IntegrityError
from config import db
from constants.library_policy import CURRENCY, CURRENCY_SCALE, POLICY_VERSION
from enums.payments.transaction_kind import TransactionKind
from enums.payments.transaction_status import TransactionStatus
from models.Book import Book
from models.Loan import Loan
from models.payments.Transaction import Transaction
from services.payments import tap_gateway
from utils.inventory import locked_book, occupied_copies
from utils.payments.errors import PaymentError
from utils.payments.money import price_minor

def start_checkout(data):
    tap_gateway.client()  # Fail closed before reserving stock when credentials are absent.
    tap_gateway.webhook_url()
    try:
        kind = TransactionKind(data.get("kind"))
        request_key = str(UUID(str(data.get("request_key"))))
    except (ValueError, TypeError):
        raise PaymentError("A valid transaction kind and UUID request_key are required")
    if data.get("accepted_terms") is not True or data.get("policy_version") != POLICY_VERSION:
        raise PaymentError("Review and accept the current library terms", 409)
    existing = Transaction.query.filter_by(user_id=g.user.user_id, request_key=request_key).first()
    if existing:
        if existing.book_slug != data.get("book_slug") or existing.kind != kind:
            raise PaymentError("Request key already used for another checkout", 409)
        return ensure_checkout(existing)
    book = Book.query.filter_by(slug=data.get("book_slug"), is_deleted=False, is_archived=False).first()
    if not book:
        raise PaymentError("Book not found", 404)
    book = locked_book(book.book_id)
    if book.is_deleted or book.is_archived:
        raise PaymentError("Book not found", 404)
    pending = Transaction.query.filter_by(user_id=g.user.user_id, book_id=book.book_id,
                                        status=TransactionStatus.PENDING.value).first()
    if pending:
        if pending.kind != kind:
            raise PaymentError("Finish or cancel your existing checkout first", 409)
        db.session.commit()
        return ensure_checkout(pending)
    if kind == TransactionKind.PURCHASE and any(user.user_id == g.user.user_id for user in book.purchased_by_users):
        raise PaymentError("Book already purchased", 409)
    if Loan.query.filter_by(book_id=book.book_id, user_id=g.user.user_id, returned_at=None,
                           is_deleted=False, is_archived=False).first():
        raise PaymentError("Return your active loan before starting checkout", 409)
    if occupied_copies(book) >= book.copies_total:
        raise PaymentError("No copies are currently available", 409)
    amount = price_minor(book.price, kind == TransactionKind.RENTAL)
    if type(data.get("expected_amount_minor")) is not int or data["expected_amount_minor"] != amount:
        raise PaymentError("Price changed; reopen the workflow to review the latest amount", 409)
    item = Transaction(user_id=g.user.user_id, book_id=book.book_id, request_key=request_key,
        kind=kind.value, amount_minor=amount,
        currency=CURRENCY, currency_scale=CURRENCY_SCALE, book_title=book.title, book_author=book.author,
        book_slug=book.slug, customer_name=g.user.user_name, policy_version=POLICY_VERSION,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=35))
    db.session.add(item)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise PaymentError("Checkout already submitted; refresh your transactions", 409)
    return ensure_checkout(item)

def ensure_checkout(item):
    if item.status != TransactionStatus.PENDING or item.provider_charge_id:
        return item
    age = datetime.now(timezone.utc) - item.created_at.replace(tzinfo=timezone.utc)
    if age >= timedelta(hours=23):
        raise PaymentError("Checkout needs administrator reconciliation before retrying", 409)
    session = tap_gateway.create_session(item)
    book = locked_book(item.book_id)
    item = Transaction.query.filter_by(transaction_id=item.transaction_id).populate_existing().with_for_update().one()
    if item.provider_charge_id and item.provider_charge_id != session["id"]:
        raise PaymentError("Provider session mismatch", 409)
    item.provider_charge_id = session["id"]
    item.checkout_url = session.get("url")
    db.session.commit()
    from utils.book_events import emit_book_changed
    emit_book_changed(book.slug, "inventory")
    from services.payments.fulfillment_service import apply_session
    return apply_session(session)
