"""Publisher profiles and catalog."""
from flask import jsonify, request

from config import db
from models.Publisher import Publisher
from utils.catalog_input import catalog_values
from utils.pagination import page_options, paginate, order_query
from utils.responses import error, success
from utils.validation import clean_text


def list_publishers():
    try:
        options = page_options()
        query = Publisher.query.filter_by(is_deleted=False, is_archived=False)
        term = clean_text(request.args.get("q"), 120)
        if term:
            query = query.filter(Publisher.name.ilike(f"%{term}%"))
        return jsonify(paginate(order_query(query, Publisher.name, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def get_publisher(publisher_id):
    item = db.session.get(Publisher, publisher_id)
    return jsonify(item.to_dict()) if item and not item.is_deleted else error("Publisher not found", 404)


def save_publisher(publisher_id=None):
    try:
        name, description, code = catalog_values()
    except ValueError as exc:
        return error(str(exc))
    item = db.session.get(Publisher, publisher_id) if publisher_id else Publisher()
    if not item or item.is_deleted:
        return error("Publisher not found", 404)
    duplicate = Publisher.query.filter_by(name=name).first()
    if duplicate and duplicate.publisher_id != item.publisher_id:
        return error("Publisher already exists", 409)
    item.name, item.description, item.country_code = name, description, code
    db.session.add(item)
    db.session.commit()
    return success("Publisher saved", 200 if publisher_id else 201, publisher=item.to_dict())
