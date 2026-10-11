"""Account registration, login, profile, and purchases."""
from flask import g, jsonify
from sqlalchemy.orm import selectinload
from werkzeug.security import check_password_hash, generate_password_hash

from config import db
from models.Book import Book
from models.User import User
from utils.pagination import page_options, paginate
from utils.responses import error, success
from utils.security import create_token
from utils.validation import clean_text, json_body, valid_password


def register():
    data = json_body()
    username = clean_text(data.get("user_name"), 80).lower()
    email = clean_text(data.get("email"), 255).lower()
    password = data.get("password")
    if len(username) < 2 or "@" not in email or not valid_password(password):
        return error("Enter a username, valid email, and password with at least 5 letters and 3 numbers")
    if User.query.filter((User.user_name == username) | (User.email == email)).first():
        return error("Username or email already exists", 409)
    user = User(user_name=username, email=email, password_digest=generate_password_hash(password), is_admin=False, is_active=True)
    db.session.add(user)
    db.session.commit()
    return success("User registered successfully", 201)


def login():
    data = json_body()
    identifier = clean_text(data.get("user_name_or_email"), 255).lower()
    password = data.get("password")
    if not identifier or not isinstance(password, str):
        return error("Invalid credentials", 401)
    user = User.query.filter((User.user_name == identifier) | (User.email == identifier)).first()
    if not user or not user.is_active or not check_password_hash(user.password_digest, password):
        return error("Invalid credentials", 401)
    return success("Login successful", token=create_token(user), user_id=user.user_id)


def profile(user_id):
    if g.user.user_id != user_id:
        return error("You can only access your own profile", 403)
    return jsonify(g.user.to_dict())


def edit_profile(user_id):
    if g.user.user_id != user_id:
        return error("You can only edit your own profile", 403)
    data = json_body()
    if "is_admin" in data or "is_active" in data:
        return error("Account roles and status cannot be changed here", 403)
    if "user_name" in data:
        username = clean_text(data["user_name"], 80).lower()
        if len(username) < 2:
            return error("Username must have at least two characters")
        if User.query.filter(User.user_name == username, User.user_id != user_id).first():
            return error("Username already exists", 409)
        g.user.user_name = username
    if "email" in data:
        email = clean_text(data["email"], 255).lower()
        if "@" not in email:
            return error("Invalid email")
        if User.query.filter(User.email == email, User.user_id != user_id).first():
            return error("Email already exists", 409)
        g.user.email = email
    if "password" in data:
        if not valid_password(data["password"]):
            return error("Password needs at least 5 letters and 3 numbers")
        g.user.password_digest = generate_password_hash(data["password"])
    db.session.commit()
    return success("Profile updated", user=g.user.to_dict())


def purchased_books(user_id):
    if g.user.user_id != user_id:
        return error("You can only view your own purchases", 403)
    try:
        query = Book.query.filter(Book.purchased_by_users.any(User.user_id == user_id)).order_by(Book.book_id.desc())
        return jsonify(paginate(query.options(selectinload(Book.reviews), selectinload(Book.loans)), lambda book: book.to_summary_dict(), page_options()))
    except ValueError as exc:
        return error(str(exc))
