"""Populate only missing profile fields in the demonstration catalog."""

from config import db
from constants.demo_catalog_profiles import DEMO_AUTHORS, DEMO_COUNTRIES, DEMO_PUBLISHERS
from models.catalog.Author import Author
from models.catalog.Country import Country
from models.catalog.Publisher import Publisher


def enrich_demo_catalog() -> None:
    for code, name in DEMO_COUNTRIES.items():
        if db.session.get(Country, code) is None:
            db.session.add(Country(code=code, name=name))
    db.session.flush()

    for name, (country_code, description) in DEMO_AUTHORS.items():
        author = Author.query.filter_by(name=name).first()
        if author is None:
            db.session.add(Author(name=name, description=description, country_code=country_code))
        elif not author.is_deleted:
            if not author.description:
                author.description = description
            if not author.country_code:
                author.country_code = country_code

    for name, description in DEMO_PUBLISHERS.items():
        publisher = Publisher.query.filter_by(name=name).first()
        if publisher is None:
            db.session.add(Publisher(name=name, description=description, country_code="US"))
        elif not publisher.is_deleted:
            if not publisher.description:
                publisher.description = description
            if not publisher.country_code:
                publisher.country_code = "US"
    db.session.flush()
