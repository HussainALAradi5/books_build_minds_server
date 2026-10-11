"""Purchase-gated review CRUD with owner and administrator moderation."""
from datetime import datetime, timezone

from flask import g, jsonify, request

from config import db
from dto.reviews.review_input_dto import ReviewInputDTO
from dto.reviews.review_update_dto import ReviewUpdateDTO
from models.reviews.Review import Review
from utils.book_events import emit_book_changed
from utils.book_lookup import visible_book
from utils.pagination import order_query, page_options, paginate
from utils.responses import error, success
from utils.validation import clean_text, json_body, valid_rating


def list_reviews(slug):
    book = visible_book(slug)
    if not book:
        return error("Book not found", 404)
    try:
        query = Review.query.filter_by(book_id=book.book_id, is_deleted=False, is_archived=False)
        term = clean_text(request.args.get("q"), 120)
        if term:
            query = query.filter(Review.comment.ilike(f"%{term}%"))
        if request.args.get("min_rating"):
            rating = valid_rating(request.args["min_rating"])
            if rating is None:
                raise ValueError("min_rating must be between 0 and 5")
            query = query.filter(Review.rating >= rating)
        sort = request.args.get("sort", "recent")
        options = page_options()
        if sort == "rating":
            query = order_query(query, Review.rating, options, Review.review_id)
        elif sort == "recent":
            query = order_query(query, Review.review_id, options)
        else:
            raise ValueError("Unsupported sort")
        return jsonify(paginate(query, lambda review: review.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def my_review(slug):
    book = visible_book(slug)
    if not book:
        return error("Book not found", 404)
    review = Review.query.filter_by(
        book_id=book.book_id, user_id=g.user.user_id, is_deleted=False, is_archived=False
    ).first()
    return jsonify({"review": review.to_dict() if review else None})


def add_review(slug):
    book = visible_book(slug)
    if not book:
        return error("Book not found", 404)
    if book not in g.user.purchased_books:
        return error("Purchase this book before reviewing it", 403)
    existing = Review.query.filter_by(
        user_id=g.user.user_id, book_id=book.book_id, is_deleted=False, is_archived=False
    ).first()
    if existing:
        return error("You already reviewed this book", 409)
    data: ReviewInputDTO = json_body()
    rating = valid_rating(data.get("rating"))
    comment = clean_text(data.get("comment"), 2000)
    description = clean_text(data.get("description"), 4000)
    if rating is None or rating < 1 or len(comment) < 10:
        return error("Rating must be 1–5 and review must have at least 10 characters")
    review = Review(
        user_id=g.user.user_id, book_id=book.book_id, rating=rating,
        comment=comment, description=description, written_time=datetime.now(timezone.utc).date(),
    )
    db.session.add(review)
    db.session.commit()
    emit_book_changed(slug, "reviews")
    return success("Review added", 201, review=review.to_dict())


def owned_review(slug, review_id):
    review = db.session.get(Review, review_id)
    if not review or review.book.slug != slug or review.is_deleted or review.is_archived:
        return None, error("Review not found for this book", 404)
    if review.user_id != g.user.user_id and not g.user.is_admin:
        return None, error("Only the author or an administrator may change this review", 403)
    return review, None


def edit_review(slug, review_id):
    review, failure = owned_review(slug, review_id)
    if failure:
        return failure
    data: ReviewUpdateDTO = json_body()
    if "rating" in data:
        rating = valid_rating(data["rating"])
        if rating is None or rating < 1:
            return error("Rating must be between 1 and 5")
        review.rating = rating
    if "comment" in data:
        comment = clean_text(data["comment"], 2000)
        if len(comment) < 10:
            return error("Review must have at least 10 characters")
        review.comment = comment
    if "description" in data:
        review.description = clean_text(data["description"], 4000)
    review.last_edit = datetime.now(timezone.utc).date()
    db.session.commit()
    emit_book_changed(slug, "reviews")
    return success("Review updated", review=review.to_dict())


def delete_review(slug, review_id):
    review, failure = owned_review(slug, review_id)
    if failure:
        return failure
    review.is_deleted = True
    db.session.commit()
    emit_book_changed(slug, "reviews")
    return success("Review deleted")
