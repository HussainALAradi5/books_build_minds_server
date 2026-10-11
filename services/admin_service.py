"""Admin promotion requests. Approval is the only role-changing path."""
from datetime import datetime, timezone
from flask import g, jsonify, request

from config import db
from models.AdminRequest import AdminRequest
from models.User import User
from utils.pagination import page_options, paginate
from utils.responses import error, success
from utils.validation import clean_text, json_body


def list_requests():
    try:
        query = AdminRequest.query
        status = request.args.get("status", "all")
        if status == "pending":
            query = query.filter(AdminRequest.is_accepted.is_(None))
        elif status == "accepted":
            query = query.filter(AdminRequest.is_accepted.is_(True))
        elif status == "rejected":
            query = query.filter(AdminRequest.is_accepted.is_(False))
        elif status != "all":
            raise ValueError("Unsupported status")
        return jsonify(paginate(query.order_by(AdminRequest.request_id.desc()), lambda item: item.to_dict(), page_options()))
    except ValueError as exc:
        return error(str(exc))


def submit_request():
    if g.user.is_admin:
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


def review_request(request_id):
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
        requester.is_admin = True
    db.session.commit()
    return success("Admin request reviewed", request=item.to_dict())
