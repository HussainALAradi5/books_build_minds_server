"""Flask API entry point. Run `flask --app app run` from server/."""
from flask import request

from config import app, db
from controllers.account import account
from controllers.admin import admin
from controllers.books import books
from controllers.media import media
from controllers.loans import loans
from controllers.reviews import reviews
import models  # noqa: F401 - registers SQLAlchemy models for migrations

for blueprint in (account, admin, books, reviews, media, loans):
    app.register_blueprint(blueprint, url_prefix="/api")


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
    app.run(debug=False)


import seed_demo  # noqa: F401 - registers CLI seed command

