"""Retry interrupted checkout, expiration, and refund processing from a scheduler."""
import click
from config import app, db
from models.payments.Transaction import Transaction
from services.payments.transaction_service import reconcile

@app.cli.command("reconcile-payments")
@click.option("--limit", default=100, type=click.IntRange(1, 1000))
def reconcile_payments(limit):
    ids = [item.transaction_id for item in Transaction.query.filter(
        Transaction.status.in_(["pending", "refund_pending"])).order_by(Transaction.created_at).limit(limit)]
    failed = 0
    for transaction_id in ids:
        try:
            item = reconcile(db.session.get(Transaction, transaction_id))
            click.echo(f"{transaction_id}: {item.status}")
        except Exception as exc:
            db.session.rollback()
            failed += 1
            click.echo(f"{transaction_id}: reconciliation failed ({type(exc).__name__}); investigate provider status", err=True)
    if failed:
        raise click.ClickException(f"{failed} transactions need retry or investigation")
