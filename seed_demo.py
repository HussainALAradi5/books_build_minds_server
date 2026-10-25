"""Idempotent development data. Run: flask --app app seed-demo."""
import os
import secrets

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from config import app, db
from enums.accounts.account_role import AccountRole
from models.catalog.Book import Book
from models.accounts.User import User
from utils.books.book_input import resolve_catalog_people
from constants.demo_book_descriptions import DEMO_BOOK_DESCRIPTIONS
from constants.demo_books import BOOKS, DEMO_BOOK_CONDITIONS, DEMO_BOOK_COPIES
from services.catalog.demo_catalog_service import enrich_demo_catalog

TEST_PASSWORDS = {
    "demo_admin": "LibraryAdmin2026!",
    "demo_employee": "LibraryStaff2026!",
    "demo_client": "LibraryReader2026!",
}


@click.command("seed-demo")
@click.option("--reset-passwords", is_flag=True, help="Generate new passwords for active demo accounts.")
@click.option("--test-accounts", is_flag=True, help="Set the documented local test account passwords.")
@with_appcontext
def seed_demo(reset_passwords: bool, test_accounts: bool):
    if os.getenv("APP_ENV") == "production":
        raise click.ClickException("Demo data cannot be seeded in production")
    db.create_all()
    demo_accounts = (
        ("demo_admin", AccountRole.ADMIN, True),
        ("demo_employee", AccountRole.EMPLOYEE, True),
        ("demo_client", AccountRole.CLIENT, True),
        ("demo_visitor", AccountRole.VISITOR, False),
    )
    for username, role, active in demo_accounts:
        email = f"{username.replace('_', '-')}@example.test"
        user = User.query.filter_by(email=email).first()
        if user and not (reset_passwords or test_accounts):
            continue
        password = TEST_PASSWORDS.get(username) if test_accounts else secrets.token_urlsafe(18)
        if password is None:
            password = secrets.token_urlsafe(18)
        if user:
            user.password_digest = generate_password_hash(password)
            user.role = role.value
            user.is_active = active
            if test_accounts:
                user.access_roles = []
                user.access_groups = []
        else:
            user = User(user_name=username, email=email, password_digest=generate_password_hash(password),
                        role=role.value, is_active=active)
            db.session.add(user)
        click.echo(f"Demo {role.value}: {username} / {password}" if active else f"Demo visitor: {username} (inactive)")
    db.session.flush()
    admin = User.query.filter_by(email="demo-admin@example.test").one()
    enrich_demo_catalog()
    for title, isbn, author, publisher, published, price in BOOKS:
        existing = Book.query.filter_by(isbn=isbn).first()
        if existing:
            if not existing.description:
                existing.description = DEMO_BOOK_DESCRIPTIONS.get(isbn, "")
            author_record, publisher_record = resolve_catalog_people(existing.author, existing.publisher)
            if existing.author_id is None:
                existing.author_id = author_record.author_id
            if existing.publisher_id is None:
                existing.publisher_id = publisher_record.publisher_id
            continue
        author_record, publisher_record = resolve_catalog_people(author, publisher)
        db.session.add(Book(title=title, description=DEMO_BOOK_DESCRIPTIONS.get(isbn, ""), slug=title.lower().replace(" ", "-"), isbn=isbn, author=author,
            publisher=publisher, author_id=author_record.author_id, publisher_id=publisher_record.publisher_id,
            published_at=published, price=price,
            copies_total=DEMO_BOOK_COPIES.get(isbn, 1),
            condition=DEMO_BOOK_CONDITIONS.get(isbn, "good"),
            added_by_user_id=admin.user_id))
    db.session.commit()
    click.echo("Demo books ready")


app.cli.add_command(seed_demo)
