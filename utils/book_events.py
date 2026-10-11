"""Public book event names and room helpers."""
from config import socketio

BOOK_CHANGED = "book_changed"


def book_room(slug: str) -> str:
    return f"book:{slug}"


def emit_book_changed(slug: str, resource: str) -> None:
    socketio.emit(BOOK_CHANGED, {"slug": slug, "resource": resource}, to=book_room(slug))
