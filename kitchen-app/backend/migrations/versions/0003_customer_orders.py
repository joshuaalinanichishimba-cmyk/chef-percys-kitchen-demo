"""Persist customer order requests and their price snapshots."""

from alembic import op
import sqlalchemy as sa

revision = "0003_customer_orders"
down_revision = "0002_menu"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_order",
        sa.Column("reference", sa.String(36), primary_key=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(24), nullable=False),
        sa.Column("fulfillment", sa.String(10), nullable=False),
        sa.Column("address", sa.String(400), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("total_ngwee", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("customer_order")
