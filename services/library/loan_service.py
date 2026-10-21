"""Loan writes serialize on the book row; paid rentals require verified checkout."""
from datetime import datetime, timedelta, timezone
from flask import g, jsonify, request
from sqlalchemy.orm import selectinload
from config import db
from constants.library_policy import BORROW_DAYS, POLICY_VERSION
from enums.library.loan_status import LoanStatus
from models.catalog.Book import Book
from models.library.Loan import Loan
from models.library.LibraryActivity import LibraryActivity
from models.payments.Transaction import Transaction
from utils.books.inventory import locked_book, occupied_copies
from utils.shared.pagination import page_options, paginate, order_query
from utils.shared.responses import error, success
from utils.shared.validation import json_body
from utils.books.book_events import emit_book_changed

def active_loan(book_id, user_id):
    return Loan.query.filter_by(book_id=book_id, user_id=user_id, returned_at=None,
                               is_deleted=False, is_archived=False).first()

def current_loan(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    loan = active_loan(book.book_id, g.user.user_id)
    return jsonify({"loan": loan.to_dict() if loan else None})

def borrow_book(slug):
    data = json_body()
    if data.get("accepted_terms") is not True or data.get("policy_version") != POLICY_VERSION:
        return error("Review and accept the current library terms", 409)
    candidate = Book.query.filter_by(slug=slug).first()
    book = locked_book(candidate.book_id) if candidate else None
    if not book or book.is_deleted or book.is_archived:
        return error("Book not found", 404)
    if active_loan(book.book_id, g.user.user_id):
        return error("You already have an active loan", 409)
    if Transaction.query.filter_by(book_id=book.book_id, user_id=g.user.user_id, status="pending").first():
        return error("Finish or cancel your checkout before borrowing", 409)
    if occupied_copies(book) >= book.copies_total:
        return error("No copies are currently available", 409)
    now = datetime.now(timezone.utc)
    loan = Loan(user_id=g.user.user_id, book_id=book.book_id, borrowed_at=now,
                due_at=now + timedelta(days=BORROW_DAYS), loan_kind="borrow", rental_fee=0,
                policy_version=POLICY_VERSION)
    db.session.add(loan)
    db.session.add(LibraryActivity(user_id=g.user.user_id, book_id=book.book_id, action_type="borrow"))
    db.session.commit()
    emit_book_changed(slug, "inventory")
    return success("Book borrowed", 201, loan=loan.to_dict())

def rent_book(slug):
    return error("Use verified payment checkout for rentals", 409)

def return_book(slug):
    candidate = Book.query.filter_by(slug=slug).first()
    book = locked_book(candidate.book_id) if candidate else None
    if not book:
        return error("Book not found", 404)
    loan = active_loan(book.book_id, g.user.user_id)
    if not loan:
        return error("You do not have an active loan for this book", 404)
    loan.returned_at = datetime.now(timezone.utc)
    db.session.add(LibraryActivity(user_id=g.user.user_id, book_id=book.book_id, action_type="return"))
    db.session.commit()
    emit_book_changed(slug, "inventory")
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
