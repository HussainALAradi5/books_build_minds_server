"""Add payment transactions receipt snapshots and loan policy

Revision ID: d0a2e93c0009
Revises: c9f1d82b0008
Create Date: 2026-10-14 23:44:34.218184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0a2e93c0009'
down_revision = 'c9f1d82b0008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('library_transaction',
    sa.Column('transaction_id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('book_id', sa.Integer(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('request_key', sa.String(length=36), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('amount_minor', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('currency_scale', sa.Integer(), nullable=False),
    sa.Column('book_title', sa.String(length=255), nullable=False),
    sa.Column('book_author', sa.String(length=255), nullable=False),
    sa.Column('customer_name', sa.String(length=80), nullable=False),
    sa.Column('book_slug', sa.String(length=255), nullable=False),
    sa.Column('policy_version', sa.String(length=32), nullable=False),
    sa.Column('provider_charge_id', sa.String(length=255), nullable=True),
    sa.Column('provider_payment_id', sa.String(length=255), nullable=True),
    sa.Column('provider_refund_id', sa.String(length=255), nullable=True),
    sa.Column('refund_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('checkout_url', sa.String(length=2048), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failure_reason', sa.String(length=255), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False),
    sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
    sa.CheckConstraint('amount_minor > 0', name='ck_transaction_amount_positive'),
    sa.ForeignKeyConstraint(['book_id'], ['book.book_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
    sa.PrimaryKeyConstraint('transaction_id'),
    sa.UniqueConstraint('provider_payment_id'),
    sa.UniqueConstraint('provider_charge_id'),
    sa.UniqueConstraint('provider_refund_id'),
    sa.UniqueConstraint('user_id', 'request_key', name='uq_transaction_request')
    )
    with op.batch_alter_table('library_transaction', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_library_transaction_book_id'), ['book_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_library_transaction_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_library_transaction_user_id'), ['user_id'], unique=False)

    op.create_table('payment_event',
    sa.Column('event_id', sa.String(length=255), nullable=False),
    sa.Column('transaction_id', sa.String(length=36), nullable=False),
    sa.Column('event_type', sa.String(length=80), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False),
    sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['transaction_id'], ['library_transaction.transaction_id'], ),
    sa.PrimaryKeyConstraint('event_id')
    )
    with op.batch_alter_table('loan', schema=None) as batch_op:
        batch_op.add_column(sa.Column('policy_version', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('transaction_id', sa.String(length=36), nullable=True))
        batch_op.create_unique_constraint('uq_loan_transaction', ['transaction_id'])
        batch_op.create_foreign_key('fk_loan_transaction', 'library_transaction', ['transaction_id'], ['transaction_id'])

    with op.batch_alter_table('receipt', schema=None) as batch_op:
        batch_op.add_column(sa.Column('transaction_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('amount_minor', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=3), nullable=True))
        batch_op.add_column(sa.Column('currency_scale', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('book_title', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('book_author', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('customer_name', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('kind', sa.String(length=16), nullable=True))
        batch_op.drop_constraint(batch_op.f('uq_receipt_user_book'), type_='unique')
        batch_op.create_unique_constraint('uq_receipt_transaction', ['transaction_id'])
        batch_op.create_foreign_key('fk_receipt_transaction', 'library_transaction', ['transaction_id'], ['transaction_id'])

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_version', sa.Integer(), server_default='0', nullable=False))



def downgrade():
    count = op.get_bind().execute(sa.text("SELECT COUNT(*) FROM library_transaction")).scalar()
    if count:
        raise RuntimeError("Cannot downgrade payment records. Back up and reconcile transactions before rollback.")
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('token_version')

    with op.batch_alter_table('receipt', schema=None) as batch_op:
        batch_op.drop_constraint('fk_receipt_transaction', type_='foreignkey')
        batch_op.drop_constraint('uq_receipt_transaction', type_='unique')
        batch_op.create_unique_constraint(batch_op.f('uq_receipt_user_book'), ['user_id', 'book_id'], postgresql_nulls_not_distinct=False)
        batch_op.drop_column('kind')
        batch_op.drop_column('customer_name')
        batch_op.drop_column('book_author')
        batch_op.drop_column('book_title')
        batch_op.drop_column('currency_scale')
        batch_op.drop_column('currency')
        batch_op.drop_column('amount_minor')
        batch_op.drop_column('transaction_id')

    with op.batch_alter_table('loan', schema=None) as batch_op:
        batch_op.drop_constraint('fk_loan_transaction', type_='foreignkey')
        batch_op.drop_constraint('uq_loan_transaction', type_='unique')
        batch_op.drop_column('transaction_id')
        batch_op.drop_column('policy_version')

    op.drop_table('payment_event')
    with op.batch_alter_table('library_transaction', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_library_transaction_user_id'))
        batch_op.drop_index(batch_op.f('ix_library_transaction_status'))
        batch_op.drop_index(batch_op.f('ix_library_transaction_book_id'))

    op.drop_table('library_transaction')
