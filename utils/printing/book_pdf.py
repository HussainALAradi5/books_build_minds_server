"""Printable catalog record; no copyrighted full book content is stored here."""
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.printing.book_codes import barcode_drawing, barcode_value, book_url, qr_drawing


def render_book_pdf(book) -> BytesIO:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    paragraph = lambda value, style="BodyText": Paragraph(escape(str(value)), styles[style])
    url = book_url(book.slug)
    code = barcode_value(book.book_id)
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=44, leftMargin=44,
                                 topMargin=42, bottomMargin=42, title=f"Book record - {book.title}",
                                 author="Books Build Minds")
    rows = [("Author", book.author), ("Publisher", book.publisher), ("ISBN", book.isbn),
            ("Published", book.published_at.isoformat()), ("Condition", book.condition.title()),
            ("Price", f"{book.price:.2f} BHD"), ("Catalog ID", code)]
    details = Table([[paragraph(label), paragraph(value)] for label, value in rows], colWidths=[100, 405])
    details.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                                ("LINEBELOW", (0, 0), (-1, -1), .3, colors.HexColor("#d1d5db"))]))
    codes = Table([[qr_drawing(url), barcode_drawing(code)],
                   [paragraph("Scan to open the book page"), paragraph("Code 128 - catalog inventory identifier")]],
                  colWidths=[200, 305])
    codes.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("ALIGN", (0, 0), (-1, 0), "CENTER")]))
    document.build([paragraph("BOOKS BUILD MINDS", "Heading2"), paragraph(book.title, "Title"),
                    paragraph("Library book record", "Heading3"), Spacer(1, 14), details,
                    Spacer(1, 26), codes, Spacer(1, 20), paragraph(url), Spacer(1, 14),
                    paragraph("Print at actual size. This barcode identifies a catalog title, not an individual physical copy.")])
    buffer.seek(0)
    return buffer
