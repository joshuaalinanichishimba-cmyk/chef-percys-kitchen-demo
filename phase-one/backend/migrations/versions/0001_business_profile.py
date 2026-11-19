"""Create the business profile and seed the approved public contact details."""

from alembic import op
import sqlalchemy as sa

revision = "0001_business_profile"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    profile = op.create_table(
        "business_profile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("contact_name", sa.String(120), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("airtel", sa.String(20), nullable=False),
        sa.Column("mtn", sa.String(20), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_business_profile_singleton"),
    )
    op.bulk_insert(profile, [{
        "id": 1,
        "name": "Chèf Percy’s Kitchen",
        "contact_name": "Percy Chanda",
        "location": "L237, CBU Campus, Kitwe",
        "airtel": "0779079908",
        "mtn": "0760892063",
    }])


def downgrade() -> None:
    op.drop_table("business_profile")
