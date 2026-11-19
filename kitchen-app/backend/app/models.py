from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, JSON, LargeBinary, String, UniqueConstraint, func
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
    status: Mapped[str] = mapped_column(String(16), server_default="received")
    customer_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(24))
    fulfillment: Mapped[str] = mapped_column(String(10))
    address: Mapped[str] = mapped_column(String(400))
    items: Mapped[list[dict]] = mapped_column(JSON)
    total_ngwee: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrderSettings(Base):
    __tablename__ = "order_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_order_settings_singleton"),
        CheckConstraint("daily_limit IS NULL OR daily_limit > 0", name="ck_order_settings_limit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    daily_limit: Mapped[int | None]


class OrderStatusEvent(Base):
    __tablename__ = "order_status_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(ForeignKey("customer_order.reference", ondelete="CASCADE"), index=True)
    actor: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CateringInquiry(Base):
    __tablename__ = "catering_inquiry"

    reference: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(24))
    event_date: Mapped[date] = mapped_column(Date)
    guests: Mapped[int]
    venue: Mapped[str] = mapped_column(String(200))
    details: Mapped[str] = mapped_column(String(800))
    status: Mapped[str] = mapped_column(String(16), server_default="received")
    quote_ngwee: Mapped[int | None] = mapped_column(BigInteger)
    deposit_ngwee: Mapped[int | None] = mapped_column(BigInteger)
    quote_notes: Mapped[str] = mapped_column(String(800), server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VerifiedPayment(Base):
    __tablename__ = "verified_payment"
    __table_args__ = (
        UniqueConstraint("channel", "transaction_reference", name="uq_verified_payment_reference"),
        CheckConstraint("amount_ngwee > 0", name="ck_verified_payment_amount"),
        CheckConstraint("num_nonnulls(order_reference, catering_reference, digital_reference) = 1", name="ck_verified_payment_target"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_reference: Mapped[str | None] = mapped_column(ForeignKey("customer_order.reference"), index=True)
    catering_reference: Mapped[str | None] = mapped_column(ForeignKey("catering_inquiry.reference"), index=True)
    digital_reference: Mapped[str | None] = mapped_column(ForeignKey("digital_purchase.reference"), unique=True)
    channel: Mapped[str] = mapped_column(String(12))
    transaction_reference: Mapped[str] = mapped_column(String(80))
    amount_ngwee: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DigitalProduct(Base):
    __tablename__ = "digital_product"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(800))
    kind: Mapped[str] = mapped_column(String(16))
    price_ngwee: Mapped[int] = mapped_column(BigInteger)
    published: Mapped[bool] = mapped_column(server_default="false")
    pdf: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)


class DigitalPurchase(Base):
    __tablename__ = "digital_purchase"

    reference: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("digital_product.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
