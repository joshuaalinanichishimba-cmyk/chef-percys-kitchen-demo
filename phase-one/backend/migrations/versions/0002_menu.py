"""Create and seed the confirmed menu poster."""

from alembic import op
import sqlalchemy as sa

revision = "0002_menu"
down_revision = "0001_business_profile"
branch_labels = None
depends_on = None

PLATTER = "Includes pita bread, fries, garlic sauce, BBQ sauce and fresh salad."
WINGS = "Extra sauce available."
ROWS = [
    ("Meals", "Shawarma Platters", "Small · 55 g chicken", PLATTER, 50),
    ("Meals", "Shawarma Platters", "Medium · 100 g chicken", PLATTER, 80),
    ("Meals", "Shawarma Platters", "Large · 150 g chicken", PLATTER, 120),
    ("Meals", "Shawarma Wraps", "Wrap only", "", 55),
    ("Meals", "Shawarma Wraps", "Wrap + fries", "", 80),
    ("Meals", "Wings & Chips", "3 wings + chips", WINGS, 70),
    ("Meals", "Wings & Chips", "6 wings + chips", WINGS, 130),
    ("Meals", "Wings & Chips", "12 wings + chips", WINGS, 230),
    ("Meals", "Hotdogs with Fries", "Chicken or beef", "Price each.", 95),
    ("Meals", "Burgers with Fries", "", "Price each.", 85),
    ("Meals", "Smoked Sausage & Chips", "", "", 60),
    ("Snacks", "Samosa", "", "", 15),
    ("Snacks", "Sausage Roll", "", "", 15),
    ("Add-ons", "Extra Garlic Sauce", "", "", 8),
    ("Add-ons", "Extra BBQ Sauce", "", "", 8),
    ("Add-ons", "Extra Pita Bread", "", "", 5),
    ("Add-ons", "Extra Fries", "Small", "", 15),
    ("Add-ons", "Extra Fries", "Large", "", 20),
    ("Add-ons", "Garlic Bread", "2 pieces", "", 15),
    ("Add-ons", "Extra Seafood", "50 g", "Ask Percy to confirm the price.", 50),
    ("Catering & Events", "Birthday Party", "", "Wings, sausages, wedges, samosas, drinks.", 2500),
    ("Catering & Events", "Picnic", "", "Mixed grill, potato salad, pies, drinks.", 3000),
    ("Catering & Events", "Corporate Event", "", "Full buffet-style spread.", 5000),
    ("Catering & Events", "Private Gathering", "", "Custom menu to suit your needs.", 2000),
]


def upgrade() -> None:
    menu = op.create_table(
        "menu_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("option", sa.String(120), nullable=False),
        sa.Column("description", sa.String(400), nullable=False),
        sa.Column("price_ngwee", sa.Integer(), nullable=False),
        sa.Column("max_price_ngwee", sa.Integer()),
        sa.Column("starting_at", sa.Boolean(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.CheckConstraint("price_ngwee > 0", name="ck_menu_entry_positive_price"),
        sa.CheckConstraint("max_price_ngwee IS NULL OR max_price_ngwee > price_ngwee", name="ck_menu_entry_price_range"),
        sa.CheckConstraint("NOT starting_at OR max_price_ngwee IS NULL", name="ck_menu_entry_price_type"),
    )
    op.bulk_insert(menu, [
        dict(category=category, name=name, option=option, description=description,
             price_ngwee=price * 100, max_price_ngwee=7000 if name == "Extra Seafood" else None,
             starting_at=category == "Catering & Events", available=True)
        for category, name, option, description, price in ROWS
    ])


def downgrade() -> None:
    op.drop_table("menu_entry")
