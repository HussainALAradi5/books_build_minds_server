"""Validate category selections against active catalog records."""
from slugify import slugify

from config import db
from models.catalog.Category import Category


def category_ids(value):
    if value is None:
        return []
    if not isinstance(value, list) or not 1 <= len(value) <= 5 or any(type(item) is not int or item < 1 for item in value):
        raise ValueError("Choose between 1 and 5 categories")
    if len(set(value)) != len(value):
        raise ValueError("Choose each category once")
    return value


def resolve_categories(ids):
    if not ids:
        category = Category.query.filter_by(slug="general", is_deleted=False, is_archived=False).first()
        if category is None:
            category = Category(name="General", slug="general")
            db.session.add(category)
            db.session.flush()
        return [category]
    items = Category.query.filter(Category.category_id.in_(ids), Category.is_deleted.is_(False), Category.is_archived.is_(False)).all()
    if len(items) != len(ids):
        raise ValueError("One or more categories do not exist")
    return items


def category_slug(name):
    slug = slugify(name)
    if not slug or len(slug) > 120:
        raise ValueError("Category name must contain letters or numbers")
    return slug
