"""Validation shared by author and publisher services."""
from config import db
from models.catalog.Country import Country
from utils.shared.validation import clean_text, json_body


def catalog_values():
    data = json_body()
    name = clean_text(data.get("name"), 255)
    description = clean_text(data.get("description"), 5000)
    code = clean_text(data.get("country_code"), 2).upper() or None
    if not name:
        raise ValueError("Name is required")
    if code and (not db.session.get(Country, code) or db.session.get(Country, code).is_deleted):
        raise ValueError("Unknown country code")
    return name, description, code
