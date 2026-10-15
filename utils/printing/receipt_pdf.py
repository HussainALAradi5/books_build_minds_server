from html import escape
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

def render_receipt(receipt):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    def paragraph(value):
        return Paragraph(escape(str(value)), styles["BodyText"])
    amount = (f"{receipt.amount_minor / receipt.currency_scale:.3f} {receipt.currency.upper()}"
              if receipt.amount_minor is not None and receipt.currency_scale else "Not recorded (legacy receipt)")
    rows = [("Receipt", f"BBM-{receipt.receipt_id:08d}"), ("Transaction", receipt.transaction_id or "Legacy purchase"),
            ("Type", receipt.kind or "purchase"), ("Book", receipt.book_title or "Legacy book record"),
            ("Author", receipt.book_author or "Not recorded"), ("Customer", receipt.customer_name or "Not recorded"),
            ("Paid", amount), ("Date", receipt.written_time.isoformat())]
    table = Table([[paragraph(key), paragraph(value)] for key, value in rows], colWidths=[100, 405])
    table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14), ("LINEBELOW", (0,0), (-1,-1), .3, colors.lightgrey)]))
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=44, rightMargin=44, title="Library payment receipt").build([
        Paragraph("Books Build Minds", styles["Title"]), Paragraph("Payment receipt", styles["Heading2"]),
        Spacer(1,18), table, Spacer(1,24), paragraph("Tap sandbox payment - no real money charged." if receipt.transaction_id else "Historical record; payment amount was not captured.")])
    buffer.seek(0)
    return buffer
