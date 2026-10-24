"""Shared pagination and query-string validation for list endpoints."""
from dataclasses import dataclass

from flask import request
from enums.shared.sort_direction import SortDirection

MAX_PAGE = 100_000


@dataclass(frozen=True)
class PageOptions:
    page: int
    per_page: int
    sort_direction: SortDirection


def page_options(default_size=12, max_size=50):
    def positive_int(name, default):
        raw = request.args.get(name, str(default))
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{name} must be a positive integer") from exc
        if value < 1:
            raise ValueError(f"{name} must be a positive integer")
        return value

    direction = request.args.get("sort_direction", SortDirection.DESC.value)
    if direction not in {item.value for item in SortDirection}:
        raise ValueError("sort_direction must be asc or desc")
    page = positive_int("page", 1)
    if page > MAX_PAGE:
        raise ValueError(f"page must be {MAX_PAGE} or less")
    return PageOptions(
        page=page,
        per_page=min(positive_int("per_page", default_size), max_size),
        sort_direction=SortDirection(direction),
    )


def order_query(query, column, options, tie_breaker=None):
    order = column.asc() if options.sort_direction == SortDirection.ASC else column.desc()
    if tie_breaker is not None and tie_breaker is not column:
        tie = tie_breaker.asc() if options.sort_direction == SortDirection.ASC else tie_breaker.desc()
        return query.order_by(order, tie)
    return query.order_by(order)

def paginate(query, serializer, options=None):
    options = options or page_options()
    result = query.paginate(page=options.page, per_page=options.per_page, error_out=False)
    return {
        "items": [serializer(item) for item in result.items],
        "pagination": {
            "page": options.page,
            "per_page": options.per_page,
            "total": result.total,
            "pages": result.pages,
            "has_next": result.has_next,
            "has_previous": result.has_prev,
        },
    }
