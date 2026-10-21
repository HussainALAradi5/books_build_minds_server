"""Small input validators used by multiple services."""
from datetime import date
from decimal import Decimal, InvalidOperation
from flask import request


def json_body():
    return request.get_json(silent=True) or {}


def clean_text(value, max_length=255):
    return value.strip()[:max_length] if isinstance(value, str) else ""


def valid_password(value):
    return (
        isinstance(value, str)
        and len(value) >= 8
        and sum(char.isalpha() for char in value) >= 5
        and sum(char.isdigit() for char in value) >= 3
    )


def valid_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def positive_price(value):
    try:
        amount = Decimal(str(value))
        return float(amount) if amount.is_finite() and amount > 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def valid_rating(value):
    try:
        rating = float(value)
        return rating if 0 <= rating <= 5 else None
    except (TypeError, ValueError):
        return None
