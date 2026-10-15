"""Inventory rules shared by borrowing, checkout, and admin updates."""
from models.Book import Book
from models.Loan import Loan
from models.payments.Transaction import Transaction
from enums.payments.transaction_status import TransactionStatus

def locked_book(book_id):
    return Book.query.filter_by(book_id=book_id).populate_existing().with_for_update().first()

def pending_count(book_id):
    # Never release a checkout reservation solely on the local clock.
    return Transaction.query.filter_by(book_id=book_id, status=TransactionStatus.PENDING.value).count()

def active_loan_count(book_id):
    return Loan.query.filter_by(book_id=book_id, returned_at=None, is_deleted=False, is_archived=False).count()

def occupied_copies(book):
    return active_loan_count(book.book_id) + len(book.purchased_by_users) + pending_count(book.book_id)

def has_open_work(book):
    return active_loan_count(book.book_id) > 0 or pending_count(book.book_id) > 0
