"""Add the PDF catalogue and protected purchase downloads."""

from alembic import op
import sqlalchemy as sa

revision = "0006_digital_library"
down_revision = "0005_catering_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "digital_product",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.String(800), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("price_ngwee", sa.BigInteger(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pdf", sa.LargeBinary()),
    )
    op.create_table(
        "digital_purchase",
        sa.Column("reference", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("digital_product.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_digital_purchase_product_id", "digital_purchase", ["product_id"])
    op.drop_constraint("ck_verified_payment_target", "verified_payment", type_="check")
    op.add_column("verified_payment", sa.Column("digital_reference", sa.String(36)))
    op.create_foreign_key(
        "fk_verified_payment_digital_reference", "verified_payment", "digital_purchase",
        ["digital_reference"], ["reference"],
    )
    op.create_unique_constraint("uq_verified_payment_digital_reference", "verified_payment", ["digital_reference"])
    op.create_check_constraint("ck_verified_payment_target", "verified_payment",
                               "num_nonnulls(order_reference, catering_reference, digital_reference) = 1")


def downgrade() -> None:
    op.drop_constraint("ck_verified_payment_target", "verified_payment", type_="check")
    op.execute("DELETE FROM verified_payment WHERE digital_reference IS NOT NULL")
    op.drop_column("verified_payment", "digital_reference")
    op.create_check_constraint("ck_verified_payment_target", "verified_payment",
                               "(order_reference IS NULL) <> (catering_reference IS NULL)")
    op.drop_table("digital_purchase")
    op.drop_table("digital_product")
