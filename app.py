"""Flask API entry point. Run `flask --app app run` from server/."""
from flask import request

from config import app, db
from config import socketio
from flask_socketio import join_room
from models.Book import Book
from utils.book_events import book_room
from controllers.account import account
from controllers.books import books
from controllers.media import media
from controllers.loans import loans
from controllers.reviews.routes import reviews
from controllers.receipts.routes import receipts
from controllers.catalog import catalog
import models  # noqa: F401 - registers SQLAlchemy models for migrations

for blueprint in (account, books, reviews, receipts, catalog, media, loans):
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
