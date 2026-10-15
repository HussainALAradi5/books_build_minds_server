"""Account registration, login, profile, purchases, and role requests."""
from datetime import datetime, timezone

from flask import g, jsonify, request
from sqlalchemy.orm import selectinload
from werkzeug.security import check_password_hash, generate_password_hash

from config import db
from models.Book import Book
from models.AdminRequest import AdminRequest
from models.LibraryActivity import LibraryActivity
from enums.library.library_action_type import LibraryActionType
from enums.accounts.admin_decision import AdminDecision
from enums.accounts.account_role import AccountRole
from models.User import User
from utils.pagination import page_options, paginate, order_query
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
    user = User(user_name=username, email=email, password_digest=generate_password_hash(password), role=AccountRole.CLIENT.value, is_active=True)
    db.session.add(user)
    db.session.flush()
    user.created_by = user.user_id
    db.session.commit()
    return success("User registered successfully", 201)


def login():
    data = json_body()
    identifier = clean_text(data.get("user_name_or_email"), 255).lower()
    password = data.get("password")
    if not identifier or not isinstance(password, str):
        return error("Invalid credentials", 401)
    user = User.query.filter((User.user_name == identifier) | (User.email == identifier)).first()
    if not user or not user.is_active or user.is_deleted or user.is_archived or not check_password_hash(user.password_digest, password):
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
    if "role" in data or "is_admin" in data or "is_active" in data:
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
        g.user.token_version += 1
    db.session.commit()
    return success("Profile updated", user=g.user.to_dict())


def purchased_books(user_id):
    if g.user.user_id != user_id:
        return error("You can only view your own purchases", 403)
    try:
        options = page_options()
        query = Book.query.filter_by(is_deleted=False, is_archived=False).filter(Book.purchased_by_users.any(User.user_id == user_id))
        return jsonify(paginate(order_query(query.options(selectinload(Book.reviews), selectinload(Book.loans)), Book.book_id, options), lambda book: book.to_summary_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def list_activities(user_id):
    if g.user.user_id != user_id:
        return error("You can only view your own activity", 403)
    try:
        options = page_options()
        query = LibraryActivity.query.filter_by(user_id=user_id, is_deleted=False, is_archived=False).options(selectinload(LibraryActivity.book))
        action = request.args.get("action", "all")
        if action != "all":
            if action not in {item.value for item in LibraryActionType}:
                raise ValueError("Unsupported action")
            query = query.filter_by(action_type=action)
        return jsonify(paginate(order_query(query, LibraryActivity.activity_id, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def list_admin_requests():
    try:
        options = page_options()
        query = AdminRequest.query.filter_by(is_deleted=False, is_archived=False)
        status = request.args.get("status", "all")
        if status == AdminDecision.PENDING.value:
            query = query.filter(AdminRequest.is_accepted.is_(None))
        elif status == AdminDecision.ACCEPTED.value:
            query = query.filter(AdminRequest.is_accepted.is_(True))
        elif status == AdminDecision.REJECTED.value:
            query = query.filter(AdminRequest.is_accepted.is_(False))
        elif status != "all":
            raise ValueError("Unsupported status")
        return jsonify(paginate(order_query(query, AdminRequest.request_id, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def submit_admin_request():
    if g.user.role == AccountRole.ADMIN.value:
        return error("Administrators cannot request admin access", 403)
    reason = clean_text(json_body().get("reason_for_request"), 2000)
    if len(reason) < 10:
        return error("Please provide a reason of at least 10 characters")
    if AdminRequest.query.filter_by(requester_id=g.user.user_id, is_accepted=None).first():
        return error("You already have a pending request", 409)
    item = AdminRequest(requester_id=g.user.user_id, reason_for_request=reason)
    db.session.add(item)
    db.session.commit()
    return success("Admin request submitted", 201, request=item.to_dict())


def review_admin_request(request_id):
    item = db.session.get(AdminRequest, request_id)
    if not item:
        return error("Admin request not found", 404)
    if item.is_accepted is not None:
        return error("Request was already reviewed", 409)
    decision = json_body().get("is_accepted")
    if type(decision) is not bool:
        return error("is_accepted must be a boolean")
    requester = db.session.get(User, item.requester_id)
    if not requester:
        return error("Requester not found", 404)
    item.is_accepted = decision
    item.review_time = datetime.now(timezone.utc).date()
    item.reviewed_by_user_id = g.user.user_id
    if decision:
        requester.role = AccountRole.ADMIN.value
    db.session.commit()
    return success("Admin request reviewed", request=item.to_dict())


def logout():
    User.query.filter_by(user_id=g.user.user_id).update({User.token_version: User.token_version + 1})
    db.session.commit()
    return success("Signed out of all sessions")
