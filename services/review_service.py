"""Book review operations with ownership checks."""
from datetime import datetime, timezone
from flask import g, jsonify, request

from config import db
from models.Book import Book
from models.Review import Review
from utils.pagination import page_options, paginate
from utils.responses import error, success
from utils.validation import clean_text, json_body, valid_rating


def list_reviews(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    try:
        query = Review.query.filter_by(book_id=book.book_id)
        if request.args.get("min_rating"):
            rating = valid_rating(request.args["min_rating"])
            if rating is None:
                raise ValueError("min_rating must be between 0 and 5")
            query = query.filter(Review.rating >= rating)
        sort = request.args.get("sort", "recent")
        if sort == "rating":
            query = query.order_by(Review.rating.desc(), Review.review_id.desc())
        elif sort == "recent":
            query = query.order_by(Review.review_id.desc())
        else:
            raise ValueError("Unsupported sort")
        return jsonify(paginate(query, lambda review: review.to_dict(), page_options()))
    except ValueError as exc:
        return error(str(exc))


def add_review(slug):
    book = Book.query.filter_by(slug=slug).first()
    if not book:
        return error("Book not found", 404)
    if book not in g.user.purchased_books:
        return error("Purchase this book before reviewing it", 403)
    if Review.query.filter_by(user_id=g.user.user_id, book_id=book.book_id).first():
        return error("You already reviewed this book", 409)
    data = json_body()
    rating = valid_rating(data.get("rating"))
    comment = clean_text(data.get("comment"), 2000)
    if rating is None or len(comment) < 10:
        return error("Rating must be 0–5 and review must have at least 10 characters")
    review = Review(user_id=g.user.user_id, book_id=book.book_id, rating=rating, comment=comment, written_time=datetime.now(timezone.utc).date())
    db.session.add(review)
    db.session.commit()
    return success("Review added", 201, review=review.to_dict())


def owned_review(slug, review_id):
    review = db.session.get(Review, review_id)
    if not review or review.book.slug != slug:
        return None, error("Review not found for this book", 404)
    if review.user_id != g.user.user_id:
        return None, error("You can only change your own review", 403)
    return review, None


def edit_review(slug, review_id):
    review, failure = owned_review(slug, review_id)
    if failure:
        return failure
    data = json_body()
    if "rating" in data:
        rating = valid_rating(data["rating"])
        if rating is None:
            return error("Rating must be between 0 and 5")
        review.rating = rating
    if "comment" in data:
        comment = clean_text(data["comment"], 2000)
        if len(comment) < 10:
            return error("Review must have at least 10 characters")
        review.comment = comment
    review.last_edit = datetime.now(timezone.utc).date()
    db.session.commit()
    return success("Review updated", review=review.to_dict())


def delete_review(slug, review_id):
    review, failure = owned_review(slug, review_id)
    if failure:
        return failure
    db.session.delete(review)
    db.session.commit()
    return success("Review deleted")
