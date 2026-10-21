"""Flask API entry point. Run `flask --app app run` from server/."""
from flask import request

from config import app, db
from config import socketio
from flask_socketio import join_room
from models.catalog.Book import Book
from utils.books.book_events import book_room
from controllers.payments.routes import payments
from controllers.accounts.account import account
from controllers.books.books import books
from controllers.media.media import media
from controllers.library.loans import loans
from controllers.reviews.routes import reviews
from controllers.receipts.routes import receipts
from controllers.catalog.catalog import catalog
from controllers.access.routes import access
import models  # noqa: F401 - registers SQLAlchemy models for migrations

for blueprint in (account, books, reviews, receipts, catalog, media, loans, access, payments):
    app.register_blueprint(blueprint, url_prefix="/api")


@socketio.on("join_book")
def join_book(data):
    slug = data.get("slug") if isinstance(data, dict) else None
    if isinstance(slug, str) and Book.query.filter_by(slug=slug, is_deleted=False, is_archived=False).first():
        join_room(book_room(slug))


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store" if request.path.startswith("/api") else "public, max-age=3600"
    return response


@app.cli.command("init-db")
def init_db():
    """Initialize a new development database. Use migrations for existing data."""
    db.create_all()
    print("Database initialized")


if __name__ == "__main__":
    socketio.run(app, debug=False)


import seed_demo  # noqa: F401 - registers CLI seed command

import services.payments.reconciliation_cli  # noqa: F401
from utils.shared.security_limits import initialize_limits
limiter = initialize_limits(app)

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError
from utils.shared.responses import error

@app.errorhandler(IntegrityError)
@app.errorhandler(StaleDataError)
def concurrent_change(_exc):
    db.session.rollback()
    return error("The record changed during your request. Refresh and retry.", 409)

@app.errorhandler(OperationalError)
def database_unavailable(_exc):
    db.session.rollback()
    return error("Database temporarily unavailable. Retry the same request.", 503)
