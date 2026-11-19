from datetime import date, datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from .menu import Database, PRIVATE, WriteRequest, owner
from .models import CateringInquiry, CustomerOrder, VerifiedPayment

router = APIRouter()
Target = Literal["orders", "catering"]
BookingStatus = Literal["received", "quoted", "booked", "completed", "cancelled"]
Channel = Literal["airtel", "mtn", "cash", "bank"]


class Inquiry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    reference: UUID4
    customer_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(pattern=r"^\+?[0-9][0-9 ()-]{6,22}$")
    event_date: date
    guests: int = Field(ge=1, le=10000, strict=True)
    venue: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=800)


class BookingView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    event_date: date
    guests: int
    status: BookingStatus
    quote_ngwee: int | None
    deposit_ngwee: int | None
    quote_notes: str
    paid_ngwee: int = 0


class OwnerBooking(BookingView):
    customer_name: str
    phone: str
    venue: str
    details: str


def paid_total(db: Database, target: Target, reference: str) -> int:
    field = VerifiedPayment.order_reference if target == "orders" else VerifiedPayment.catering_reference
    return int(db.scalar(select(func.coalesce(func.sum(VerifiedPayment.amount_ngwee), 0)).where(field == reference)))


def booking_view(db: Database, item: CateringInquiry) -> BookingView:
    return BookingView.model_validate(item).model_copy(update={"paid_ngwee": paid_total(db, "catering", item.reference)})


@router.post("/api/catering", status_code=201, response_model=BookingView)
def create_inquiry(data: Inquiry, db: Database, response: Response):
    reference = str(data.reference)
    fields = data.model_dump(exclude={"reference"})
    item = db.get(CateringInquiry, reference)
    if item is None:
        if data.event_date < datetime.now(timezone(timedelta(hours=2))).date():
            raise HTTPException(422, "Choose today or a future event date.")
        db.execute(insert(CateringInquiry).values(reference=reference, **fields)
                   .on_conflict_do_nothing(index_elements=[CateringInquiry.reference]))
        item = db.get_one(CateringInquiry, reference)
    if any(getattr(item, key) != value for key, value in fields.items()):
        raise HTTPException(409, "This inquiry reference has already been used.")
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return booking_view(db, item)


@router.get("/api/catering/{reference}", response_model=BookingView)
def public_booking(reference: UUID, db: Database, response: Response):
    item = db.get(CateringInquiry, str(reference))
    if item is None:
        raise HTTPException(404, "Catering reference not found.")
    response.headers["Cache-Control"] = "no-store"
    return booking_view(db, item)


@owner.get("/owner/api/catering", response_model=list[OwnerBooking])
def owner_bookings(db: Database, response: Response):
    response.headers.update(PRIVATE)
    items = db.scalars(select(CateringInquiry).order_by(CateringInquiry.created_at.desc()).limit(50))
    return [OwnerBooking.model_validate(item).model_copy(
        update={"paid_ngwee": paid_total(db, "catering", item.reference)}
    ) for item in items]


class Quote(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    quote_ngwee: int = Field(gt=0, le=100_000_000, strict=True)
    deposit_ngwee: int = Field(ge=0, le=100_000_000, strict=True)
    quote_notes: str = Field(default="", max_length=800)


def lock_booking(db: Database, reference: UUID) -> CateringInquiry:
    item = db.get(CateringInquiry, str(reference), with_for_update=True)
    if item is None:
        raise HTTPException(404, "Catering reference not found.", headers=PRIVATE)
    return item


@owner.put("/owner/api/catering/{reference}/quote", response_model=BookingView, dependencies=[WriteRequest])
def save_quote(reference: UUID, data: Quote, db: Database, response: Response):
    item = lock_booking(db, reference)
    if item.status not in ("received", "quoted"):
        raise HTTPException(409, "Only open inquiries can be quoted.", headers=PRIVATE)
    if data.deposit_ngwee > data.quote_ngwee:
        raise HTTPException(422, "The deposit cannot exceed the quote.", headers=PRIVATE)
    if data.quote_ngwee < paid_total(db, "catering", item.reference):
        raise HTTPException(409, "The quote cannot be lower than payments already recorded.", headers=PRIVATE)
    item.quote_ngwee = data.quote_ngwee
    item.deposit_ngwee = data.deposit_ngwee
    item.quote_notes = data.quote_notes
    item.status = "quoted"
    db.commit()
    response.headers.update(PRIVATE)
    return booking_view(db, item)


class BookingAction(BaseModel):
    status: Literal["booked", "completed", "cancelled"]


@owner.put("/owner/api/catering/{reference}/status", response_model=BookingView, dependencies=[WriteRequest])
def booking_status(reference: UUID, data: BookingAction, db: Database, response: Response):
    item = lock_booking(db, reference)
    transitions = {"received": ("cancelled",), "quoted": ("booked", "cancelled"), "booked": ("completed", "cancelled")}
    if data.status not in transitions.get(item.status, ()):
        raise HTTPException(409, "That status change is unavailable.", headers=PRIVATE)
    if data.status == "booked" and paid_total(db, "catering", item.reference) < (item.deposit_ngwee or 0):
        raise HTTPException(409, "Record the verified deposit before booking.", headers=PRIVATE)
    item.status = data.status
    db.commit()
    response.headers.update(PRIVATE)
    return booking_view(db, item)


class PaymentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    channel: Channel
    transaction_reference: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,79}$")
    amount_ngwee: int = Field(gt=0, le=100_000_000, strict=True)
    verified: bool = Field(strict=True)

    @field_validator("verified")
    @classmethod
    def require_verification(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Confirm that you verified the payment.")
        return value


class PaymentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel: Channel
    transaction_reference: str
    amount_ngwee: int
    created_at: datetime


@owner.get("/owner/api/payments/{target}/{reference}", response_model=list[PaymentView])
def payment_list(target: Target, reference: UUID, db: Database, response: Response):
    field = VerifiedPayment.order_reference if target == "orders" else VerifiedPayment.catering_reference
    response.headers.update(PRIVATE)
    return db.scalars(select(VerifiedPayment).where(field == str(reference)).order_by(VerifiedPayment.id)).all()


@owner.post("/owner/api/payments/{target}/{reference}", response_model=PaymentView, status_code=201, dependencies=[WriteRequest])
def record_payment(target: Target, reference: UUID, data: PaymentInput, db: Database, response: Response):
    key = str(reference)
    if target == "orders":
        order = db.get(CustomerOrder, key, with_for_update=True)
        if order is None:
            raise HTTPException(404, "Order not found.", headers=PRIVATE)
        amount, status = order.total_ngwee, order.status
    else:
        booking = lock_booking(db, reference)
        amount, status = booking.quote_ngwee, booking.status

    transaction = data.transaction_reference.upper()
    match = select(VerifiedPayment).where(VerifiedPayment.channel == data.channel,
                                         VerifiedPayment.transaction_reference == transaction)
    existing = db.scalar(match)
    if existing is None:
        if status == "cancelled" or amount is None:
            raise HTTPException(409, "Record payments only against an active order or a saved quote.", headers=PRIVATE)
        if paid_total(db, target, key) + data.amount_ngwee > amount:
            raise HTTPException(409, "This amount exceeds the outstanding balance.", headers=PRIVATE)
        db.execute(insert(VerifiedPayment).values(
            channel=data.channel, transaction_reference=transaction, amount_ngwee=data.amount_ngwee,
            order_reference=key if target == "orders" else None,
            catering_reference=key if target == "catering" else None,
        ).on_conflict_do_nothing(constraint="uq_verified_payment_reference"))
        existing = db.scalars(match).one()

    linked = existing.order_reference if target == "orders" else existing.catering_reference
    if linked != key or existing.amount_ngwee != data.amount_ngwee:
        raise HTTPException(409, "This transaction reference was already recorded.", headers=PRIVATE)
    db.commit()
    response.headers.update(PRIVATE)
    return existing
