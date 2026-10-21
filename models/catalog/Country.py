"""Locally cached country reference data from REST Countries."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from config import db
from models.shared.BaseEntity import BaseEntity
from dto.catalog.country_dto import CountryDTO


class Country(BaseEntity, db.Model):
    __tablename__ = "country"

    code = Column(String(2), primary_key=True)
    name = Column(String(120), nullable=False)
    flag_url = Column(String(500))

    authors = relationship("Author", back_populates="country")
    publishers = relationship("Publisher", back_populates="country")

    def to_dict(self) -> CountryDTO:
        return {"code": self.code, "name": self.name, "flag_url": self.flag_url,
                **self.entity_dict(),}
