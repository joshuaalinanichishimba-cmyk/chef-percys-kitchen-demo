from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, JSON, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BusinessProfile(Base):
    __tablename__ = "business_profile"
    __table_args__ = (CheckConstraint("id = 1", name="ck_business_profile_singleton"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(150))
    contact_name: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(200))
    airtel: Mapped[str] = mapped_column(String(20))
    mtn: Mapped[str] = mapped_column(String(20))


class MenuEntry(Base):
    __tablename__ = "menu_entry"
    __table_args__ = (
        CheckConstraint("price_ngwee > 0", name="ck_menu_entry_positive_price"),
        CheckConstraint("max_price_ngwee IS NULL OR max_price_ngwee > price_ngwee", name="ck_menu_entry_price_range"),
        CheckConstraint("NOT starting_at OR max_price_ngwee IS NULL", name="ck_menu_entry_price_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(120))
    option: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(400))
    price_ngwee: Mapped[int]
    max_price_ngwee: Mapped[int | None]
    starting_at: Mapped[bool]
    available: Mapped[bool]


class CustomerOrder(Base):
    __tablename__ = "customer_order"

    reference: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    customer_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(24))
    fulfillment: Mapped[str] = mapped_column(String(10))
    address: Mapped[str] = mapped_column(String(400))
    items: Mapped[list[dict]] = mapped_column(JSON)
    total_ngwee: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
