"""Add order status, status history and daily capacity settings."""

from alembic import op
import sqlalchemy as sa

revision = "0004_kitchen_workflow"
down_revision = "0003_customer_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customer_order", sa.Column("status", sa.String(16), server_default="received", nullable=False))
    settings = op.create_table(
        "order_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("daily_limit", sa.Integer()),
        sa.CheckConstraint("id = 1", name="ck_order_settings_singleton"),
        sa.CheckConstraint("daily_limit IS NULL OR daily_limit > 0", name="ck_order_settings_limit"),
    )
    op.bulk_insert(settings, [{"id": 1, "daily_limit": None}])
    op.create_table(
        "order_status_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(36), sa.ForeignKey("customer_order.reference", ondelete="CASCADE"), nullable=False),
        sa.Column("actor", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_order_status_event_reference", "order_status_event", ["reference"])


def downgrade() -> None:
    op.drop_table("order_status_event")
    op.drop_table("order_settings")
    op.drop_column("customer_order", "status")
