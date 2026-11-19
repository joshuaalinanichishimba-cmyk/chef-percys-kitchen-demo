"""Add catering inquiries, quotes and manually verified payment records."""

from alembic import op
import sqlalchemy as sa

revision = "0005_catering_payments"
down_revision = "0004_kitchen_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catering_inquiry",
        sa.Column("reference", sa.String(36), primary_key=True),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(24), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("guests", sa.Integer(), nullable=False),
        sa.Column("venue", sa.String(200), nullable=False),
        sa.Column("details", sa.String(800), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="received"),
        sa.Column("quote_ngwee", sa.BigInteger()),
        sa.Column("deposit_ngwee", sa.BigInteger()),
        sa.Column("quote_notes", sa.String(800), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "verified_payment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_reference", sa.String(36), sa.ForeignKey("customer_order.reference")),
        sa.Column("catering_reference", sa.String(36), sa.ForeignKey("catering_inquiry.reference")),
        sa.Column("channel", sa.String(12), nullable=False),
        sa.Column("transaction_reference", sa.String(80), nullable=False),
        sa.Column("amount_ngwee", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("channel", "transaction_reference", name="uq_verified_payment_reference"),
        sa.CheckConstraint("amount_ngwee > 0", name="ck_verified_payment_amount"),
        sa.CheckConstraint("(order_reference IS NULL) <> (catering_reference IS NULL)", name="ck_verified_payment_target"),
    )
    op.create_index("ix_verified_payment_order_reference", "verified_payment", ["order_reference"])
    op.create_index("ix_verified_payment_catering_reference", "verified_payment", ["catering_reference"])


def downgrade() -> None:
    op.drop_table("verified_payment")
    op.drop_table("catering_inquiry")
