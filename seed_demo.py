"""Idempotent development data. Run: flask --app app seed-demo."""
import os
import secrets
from datetime import date

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from config import app, db
from models.Book import Book
from models.User import User

BOOKS = [
    ("The Midnight Library", "9780525559474", "Matt Haig", "Viking", date(2020, 9, 29), 7.50),
    ("Atomic Habits", "9780735211292", "James Clear", "Avery", date(2018, 10, 16), 8.90),
    ("The Alchemist", "9780062315007", "Paulo Coelho", "HarperOne", date(2014, 4, 15), 5.25),
    ("Educated", "9780399590504", "Tara Westover", "Random House", date(2018, 2, 20), 9.75),
    ("Deep Work", "9781455586691", "Cal Newport", "Grand Central", date(2016, 1, 5), 6.80),
    ("Sapiens", "9780062316097", "Yuval Noah Harari", "Harper", date(2015, 2, 10), 10.20),
]


@click.command("seed-demo")
@with_appcontext
def seed_demo():
    if os.getenv("APP_ENV") == "production":
        raise click.ClickException("Demo data cannot be seeded in production")
    db.create_all()
    admin = User.query.filter_by(email="demo-admin@example.test").first()
    if not admin:
        password = secrets.token_urlsafe(18)
        admin = User(user_name="demo_admin", email="demo-admin@example.test", password_digest=generate_password_hash(password), is_admin=True, is_active=True)
        db.session.add(admin)
        db.session.flush()
        click.echo(f"Demo admin: demo_admin / {password}")
    for title, isbn, author, publisher, published, price in BOOKS:
        if Book.query.filter_by(isbn=isbn).first():
            continue
        db.session.add(Book(title=title, slug=title.lower().replace(" ", "-"), isbn=isbn, author=author, publisher=publisher, published_at=published, price=price, added_by_user_id=admin.user_id))
    db.session.commit()
    click.echo("Demo books ready")


app.cli.add_command(seed_demo)
