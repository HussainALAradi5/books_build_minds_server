"""Validate, store, and list book images on the server."""
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from flask import g, jsonify, request
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from config import BASE_DIR, db
from enums.media.media_type import MediaType
from models.catalog.Book import Book
from models.media.Media import Media
from utils.shared.pagination import page_options, paginate, order_query
from utils.shared.responses import error, success

MEDIA_DIR = BASE_DIR / "static" / "media"
MAX_FILES = 10
MAX_FILE_BYTES = 5 * 1024 * 1024
SUPPORTED = {"JPEG": ("jpg", "image/jpeg"), "PNG": ("png", "image/png"), "GIF": ("gif", "image/gif"), "WEBP": ("webp", "image/webp")}


def list_media(book_id):
    book = db.session.get(Book, book_id)
    if not book or book.is_deleted or book.is_archived:
        return error("Book not found", 404)
    try:
        options = page_options()
        query = Media.query.filter_by(book_id=book_id, is_deleted=False, is_archived=False)
        return jsonify(paginate(order_query(query, Media.media_id, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def validate_file(file):
    content = file.read(MAX_FILE_BYTES + 1)
    if not content or len(content) > MAX_FILE_BYTES:
        raise ValueError("Each image must be between 1 byte and 5 MB")
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
            image_format = image.format
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Invalid image file") from exc
    if image_format not in SUPPORTED:
        raise ValueError("Only JPEG, PNG, GIF, and WebP images are supported")
    extension, mime_type = SUPPORTED[image_format]
    return content, extension, mime_type


def upload_media(book_id):
    book = db.session.get(Book, book_id)
    if not book or book.is_deleted or book.is_archived:
        return error("Book not found", 404)
    files = request.files.getlist("files")
    if not 1 <= len(files) <= MAX_FILES:
        return error("Upload between 1 and 10 images")
    validated = []
    try:
        for file in files:
            content, extension, mime_type = validate_file(file)
            validated.append((content, extension, mime_type, secure_filename(file.filename or "image")[:255]))
    except ValueError as exc:
        return error(str(exc))

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    items = []
    try:
        for content, extension, mime_type, original_name in validated:
            filename = f"{uuid4().hex}.{extension}"
            path = MEDIA_DIR / filename
            path.write_bytes(content)
            saved_paths.append(path)
            item = Media(book_id=book_id, media_type=MediaType.BOOK_COVER.value if not book.book_image and not items else MediaType.BOOK_GALLERY.value, uploaded_by_user_id=g.user.user_id, filename=filename,
                         original_name=original_name, mime_type=mime_type, size_bytes=len(content))
            db.session.add(item)
            items.append(item)
        if not book.book_image:
            book.book_image = f"/static/media/{items[0].filename}"
        db.session.commit()
        return success("Media uploaded", 201, items=[item.to_dict() for item in items])
    except Exception:
        db.session.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise


def upload_profile_picture():
    files = request.files.getlist("files")
    if len(files) != 1:
        return error("Upload exactly one profile image")
    try:
        content, extension, mime_type = validate_file(files[0])
    except ValueError as exc:
        return error(str(exc))
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.{extension}"
    path = MEDIA_DIR / filename
    try:
        path.write_bytes(content)
        item = Media(user_id=g.user.user_id, media_type=MediaType.PROFILE_PICTURE.value,
                     uploaded_by_user_id=g.user.user_id, filename=filename,
                     original_name=secure_filename(files[0].filename or "profile")[:255],
                     mime_type=mime_type, size_bytes=len(content))
        db.session.add(item)
        db.session.commit()
        return success("Profile picture uploaded", 201, media=item.to_dict(), user=g.user.to_dict())
    except Exception:
        db.session.rollback()
        path.unlink(missing_ok=True)
        raise
