"""Server-generated vector codes with quiet zones and stable catalog identifiers."""
from base64 import b64encode
import re
from urllib.parse import quote, urlsplit

from flask import current_app
from reportlab.graphics import renderSVG
from reportlab.lib.colors import white
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing, Rect

from enums.books.barcode_type import BarcodeType


def book_url(slug: str) -> str:
    origin = current_app.config["PUBLIC_CLIENT_URL"].rstrip("/")
    parsed = urlsplit(origin)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("PUBLIC_CLIENT_URL must be an absolute HTTP(S) URL without credentials, query, or fragment")
    return f"{origin}/book/{quote(slug, safe='')}"


def barcode_value(book_id: int) -> str:
    return f"BBM-{book_id:08d}"


def qr_drawing(value: str, size: int = 144) -> Drawing:
    widget = QrCodeWidget(value, barLevel="M", barBorder=4)
    x1, y1, x2, y2 = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0])
    drawing.add(Rect(0, 0, x2 - x1, y2 - y1, fillColor=white, strokeColor=None))
    drawing.add(widget)
    return drawing


def barcode_drawing(value: str) -> Drawing:
    return createBarcodeDrawing(BarcodeType.CODE128.value, value=value, barHeight=52,
                                barWidth=1.2, humanReadable=True, quiet=True)


def svg_data_url(drawing: Drawing) -> str:
    svg = renderSVG.drawToString(drawing)
    return "data:image/svg+xml;base64," + b64encode(svg.encode("utf-8")).decode("ascii")


def parse_barcode(value: str) -> int | None:
    match = re.fullmatch(r"BBM-([0-9]{8,18})", value.strip())
    return int(match.group(1)) if match else None
