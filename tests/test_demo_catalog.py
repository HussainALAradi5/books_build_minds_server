"""Demo catalog enrichment must preserve manually edited creator profiles."""

import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-long-enough-for-hs256"

from app import app  # noqa: E402
from config import db  # noqa: E402
from models.catalog.Author import Author  # noqa: E402
from models.catalog.Publisher import Publisher  # noqa: E402
from services.catalog.demo_catalog_service import enrich_demo_catalog  # noqa: E402


class DemoCatalogTests(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_profiles_are_populated_without_overwriting_edits(self):
        enrich_demo_catalog()
        db.session.commit()
        author = Author.query.filter_by(name="Matt Haig").one()
        publisher = Publisher.query.filter_by(name="Viking").one()
        self.assertTrue(author.description)
        self.assertEqual(author.country_code, "GB")
        self.assertTrue(publisher.description)
        self.assertEqual(publisher.country_code, "US")

        author.description = "Custom author biography"
        publisher.country_code = "GB"
        db.session.commit()
        enrich_demo_catalog()
        db.session.commit()

        self.assertEqual(Author.query.filter_by(name="Matt Haig").count(), 1)
        self.assertEqual(Publisher.query.filter_by(name="Viking").count(), 1)
        self.assertEqual(author.description, "Custom author biography")
        self.assertEqual(publisher.country_code, "GB")
