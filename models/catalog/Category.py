"""Reusable categories assigned to one or more books."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from config import db
from models.shared.BaseEntity import BaseEntity

book_categories = db.Table(
    "book_categories",
    db.Column("book_id", Integer, db.ForeignKey("book.book_id"), primary_key=True),
    db.Column("category_id", Integer, db.ForeignKey("category.category_id"), primary_key=True),
)


class Category(BaseEntity, db.Model):
    __tablename__ = "category"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True)
    slug = Column(String(120), nullable=False, unique=True)
    books = relationship("Book", secondary=book_categories, back_populates="categories")

    def to_dict(self):
        return {"category_id": self.category_id, "name": self.name, "slug": self.slug, **self.entity_dict()}
