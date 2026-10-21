"""Book publisher and its catalog."""
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from config import db
from models.shared.BaseEntity import BaseEntity
from dto.catalog.publisher_dto import PublisherDTO


class Publisher(BaseEntity, db.Model):
    __tablename__ = "publisher"

    publisher_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False, default="")
    country_code = Column(String(2), ForeignKey("country.code"))

    country = relationship("Country", back_populates="publishers")
    books = relationship("Book", back_populates="publisher_record")

    def to_dict(self) -> PublisherDTO:
        return {"publisher_id": self.publisher_id, "name": self.name, "description": self.description,
                "country": self.country.to_dict() if self.country else None,
                "works": [{"book_id": book.book_id, "slug": book.slug, "title": book.title}
                          for book in self.books if not book.is_deleted and not book.is_archived],
                **self.entity_dict(),}
