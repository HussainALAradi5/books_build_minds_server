from flask import jsonify, request

from utils.shared.pagination import order_query, page_options, paginate
from utils.shared.responses import error
from utils.shared.validation import clean_text


def list_records(model, search_column, sort_column):
    try:
        options = page_options(default_size=25, max_size=100)
        query = model.query.filter_by(is_deleted=False, is_archived=False)
        term = clean_text(request.args.get("q"), 120)
        if term:
            query = query.filter(search_column.ilike(f"%{term}%"))
        return jsonify(paginate(order_query(query, sort_column, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))
