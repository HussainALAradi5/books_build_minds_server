"""Rank books from persisted reviews and completed purchases."""
from sqlalchemy import func

from config import db
from models.catalog.Book import Book
from models.reviews.Review import Review
from models.payments.Transaction import Transaction
from enums.payments.transaction_kind import TransactionKind
from enums.payments.transaction_status import TransactionStatus


def ranked_books(query, sort):
    if sort == "most_rated":
        ratings = db.session.query(Review.book_id, func.avg(Review.rating).label("score"),
            func.count(Review.review_id).label("votes")).filter_by(is_deleted=False, is_archived=False).group_by(Review.book_id).subquery()
        return query.outerjoin(ratings, Book.book_id == ratings.c.book_id).order_by(
            func.coalesce(ratings.c.score, 0).desc(), func.coalesce(ratings.c.votes, 0).desc(), Book.book_id.desc())
    if sort == "best_selling":
        sales = db.session.query(Transaction.book_id, func.count(Transaction.transaction_id).label("sales")).filter(
            Transaction.kind == TransactionKind.PURCHASE.value, Transaction.status == TransactionStatus.COMPLETED.value,
            Transaction.is_deleted.is_(False)).group_by(Transaction.book_id).subquery()
        return query.outerjoin(sales, Book.book_id == sales.c.book_id).order_by(
            func.coalesce(sales.c.sales, 0).desc(), Book.book_id.desc())
    raise ValueError("Unsupported ranking")
