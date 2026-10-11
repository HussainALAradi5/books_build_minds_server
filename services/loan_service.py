"""Borrowing, returning, and paginated loan history."""
from datetime import datetime, timedelta, timezone

from flask import g, jsonify, request
from sqlalchemy.orm import selectinload

from config import db
from enums.library.loan_status import LoanStatus
from enums.library.library_action_type import LibraryActionType
from enums.library.loan_kind import LoanKind
from models.Book import Book
from models.Loan import Loan
from models.LibraryActivity import LibraryActivity
from utils.pagination import page_options, paginate, order_query
from utils.responses import error, success

LOAN_DAYS = 14


def active_loan(book_id, user_id):
    return Loan.query.filter_by(book_id=book_id, user_id=user_id, returned_at=None).first()


def current_loan(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    loan = active_loan(book.book_id, g.user.user_id)
    return jsonify({"loan": loan.to_dict() if loan else None})


def borrow_book(slug):
    return start_loan(slug, LoanKind.BORROW)


def rent_book(slug):
    return start_loan(slug, LoanKind.RENT)


def start_loan(slug, kind):
    book = Book.query.filter_by(slug=slug).with_for_update().first()
    if not book:
        return error("Book not found", 404)
    if active_loan(book.book_id, g.user.user_id):
        return error("You already borrowed this book", 409)
    active_count = Loan.query.filter_by(book_id=book.book_id, returned_at=None).count()
    if active_count >= book.copies_total:
        return error("No copies are currently available", 409)
    now = datetime.now(timezone.utc)
    days = 7 if kind == LoanKind.RENT else LOAN_DAYS
    fee = round(book.price * 0.2, 2) if kind == LoanKind.RENT else 0
    loan = Loan(user_id=g.user.user_id, book_id=book.book_id, borrowed_at=now, due_at=now + timedelta(days=days), loan_kind=kind.value, rental_fee=fee)
    db.session.add(loan)
    db.session.add(LibraryActivity(user_id=g.user.user_id, book_id=book.book_id, action_type=kind.value))
    db.session.commit()
    return success("Book rented" if kind == LoanKind.RENT else "Book borrowed", 201, loan=loan.to_dict())


def return_book(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    loan = active_loan(book.book_id, g.user.user_id)
    if not loan:
        return error("You do not have an active loan for this book", 404)
    loan.returned_at = datetime.now(timezone.utc)
    db.session.add(LibraryActivity(user_id=g.user.user_id, book_id=book.book_id, action_type=LibraryActionType.RETURN.value))
    db.session.commit()
    return success("Book returned", loan=loan.to_dict())


def list_loans(user_id):
    if user_id != g.user.user_id:
        return error("You can only view your own loans", 403)
    try:
        options = page_options()
        query = Loan.query.filter_by(user_id=user_id, is_deleted=False, is_archived=False).options(selectinload(Loan.book))
        status = request.args.get("status", "all")
        if status == LoanStatus.ACTIVE.value:
            query = query.filter(Loan.returned_at.is_(None), Loan.due_at >= datetime.now(timezone.utc))
        elif status == LoanStatus.OVERDUE.value:
            query = query.filter(Loan.returned_at.is_(None), Loan.due_at < datetime.now(timezone.utc))
        elif status == LoanStatus.RETURNED.value:
            query = query.filter(Loan.returned_at.is_not(None))
        elif status != "all":
            raise ValueError("Unsupported loan status")
        return jsonify(paginate(order_query(query, Loan.loan_id, options), lambda loan: loan.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))
