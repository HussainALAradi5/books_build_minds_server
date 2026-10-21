"""Shared audit fields and lifecycle flags for persisted library records."""
from datetime import datetime, timezone

from flask import g, has_request_context
from sqlalchemy import Boolean, Column, DateTime, Integer, event, func
from sqlalchemy.orm import Session

from enums.shared.generic_status import GenericStatus


class BaseEntity:
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False, server_default="0")
    is_deleted = Column(Boolean, nullable=False, default=False, server_default="0")

    def entity_dict(self) -> dict:
        return {
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_archived": self.is_archived,
            "is_deleted": self.is_deleted,
        }

    @property
    def status(self) -> GenericStatus:
        if self.is_deleted:
            return GenericStatus.DELETED
        if self.is_archived:
            return GenericStatus.ARCHIVED
        return GenericStatus.ACTIVE


@event.listens_for(Session, "before_flush")
def stamp_entity_changes(session, _flush_context, _instances):
    actor = getattr(g, "user", None) if has_request_context() else None
    actor_id = getattr(actor, "user_id", None)
    now = datetime.now(timezone.utc)
    for entity in session.new:
        if isinstance(entity, BaseEntity):
            if entity.created_at is None:
                entity.created_at = now
            if entity.created_by is None:
                entity.created_by = actor_id
    for entity in session.dirty:
        if isinstance(entity, BaseEntity) and session.is_modified(entity, include_collections=False):
            entity.updated_at = now
            entity.updated_by = actor_id
