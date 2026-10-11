"""Shared pagination and query-string validation for list endpoints."""
from dataclasses import dataclass

from flask import request


@dataclass(frozen=True)
class PageOptions:
    page: int
    per_page: int


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

    return PageOptions(
        page=positive_int("page", 1),
        per_page=min(positive_int("per_page", default_size), max_size),
    )


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
