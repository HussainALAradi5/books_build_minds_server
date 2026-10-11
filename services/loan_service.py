"""Borrowing, returning, and paginated loan history."""
from datetime import datetime, timedelta, timezone

from flask import g, jsonify, request
from sqlalchemy.orm import selectinload

from config import db
from enums import LoanStatus
from models.Book import Book
from models.Loan import Loan
from utils.pagination import page_options, paginate
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
    book = Book.query.filter_by(slug=slug).with_for_update().first()
    if not book:
        return error("Book not found", 404)
    if active_loan(book.book_id, g.user.user_id):
        return error("You already borrowed this book", 409)
    active_count = Loan.query.filter_by(book_id=book.book_id, returned_at=None).count()
    if active_count >= book.copies_total:
        return error("No copies are currently available", 409)
    now = datetime.now(timezone.utc)
    loan = Loan(user_id=g.user.user_id, book_id=book.book_id, borrowed_at=now, due_at=now + timedelta(days=LOAN_DAYS))
    db.session.add(loan)
    db.session.commit()
    return success("Book borrowed", 201, loan=loan.to_dict())


def return_book(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    loan = active_loan(book.book_id, g.user.user_id)
    if not loan:
        return error("You do not have an active loan for this book", 404)
    loan.returned_at = datetime.now(timezone.utc)
    db.session.commit()
    return success("Book returned", loan=loan.to_dict())


def list_loans(user_id):
    if user_id != g.user.user_id:
        return error("You can only view your own loans", 403)
    try:
        query = Loan.query.filter_by(user_id=user_id).options(selectinload(Loan.book))
        status = request.args.get("status", "all")
        if status == LoanStatus.ACTIVE.value:
            query = query.filter(Loan.returned_at.is_(None), Loan.due_at >= datetime.now(timezone.utc))
        elif status == LoanStatus.OVERDUE.value:
            query = query.filter(Loan.returned_at.is_(None), Loan.due_at < datetime.now(timezone.utc))
        elif status == LoanStatus.RETURNED.value:
            query = query.filter(Loan.returned_at.is_not(None))
        elif status != "all":
            raise ValueError("Unsupported loan status")
        return jsonify(paginate(query.order_by(Loan.loan_id.desc()), lambda loan: loan.to_dict(), page_options()))
    except ValueError as exc:
        return error(str(exc))
