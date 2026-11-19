from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Annotated, Literal
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from .menu import CSP, Database, PRIVATE, WriteRequest, owner
from .bookings import paid_total
from .models import CustomerOrder, MenuEntry, OrderSettings, OrderStatusEvent
from .owner_auth import require_kitchen

router = APIRouter()
kitchen = APIRouter(dependencies=[Depends(require_kitchen)], include_in_schema=False)
KITCHEN_FILES = Path(__file__).with_name("kitchen")
KITWE = timezone(timedelta(hours=2))
Status = Literal["received", "confirmed", "preparing", "ready", "completed", "cancelled"]
NEXT = {
    "received": ("confirmed", "cancelled"),
    "confirmed": ("preparing", "cancelled"),
    "preparing": ("ready", "cancelled"),
    "ready": ("completed", "cancelled"),
}
KITCHEN_STEPS = {"confirmed": ("preparing",), "preparing": ("ready",)}


class OrderLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    menu_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=20)
    expected_price_ngwee: int = Field(gt=0)


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reference: UUID
    customer_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(pattern=r"^\+?[0-9][0-9 ()-]{6,22}$")
    fulfillment: Literal["pickup", "delivery"]
    address: str = Field(default="", max_length=400)
    lines: Annotated[list[OrderLine], Field(min_length=1, max_length=30)]

    @model_validator(mode="after")
    def check_delivery_and_lines(self):
        if self.reference.version != 4:
            raise ValueError("Use a version 4 order reference.")
        if self.fulfillment == "delivery" and not self.address:
            raise ValueError("A delivery address is required.")
        if len({line.menu_id for line in self.lines}) != len(self.lines):
            raise ValueError("Combine quantities for identical items.")
        return self


class ReceiptLine(BaseModel):
    name: str
    option: str
    quantity: int
    unit_price_ngwee: int


class Receipt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    fulfillment: Literal["pickup", "delivery"]
    items: list[ReceiptLine]
    total_ngwee: int
    created_at: datetime
    status: Status
    paid_ngwee: int = 0


class OwnerOrder(Receipt):
    customer_name: str
    phone: str
    address: str


def match_request(order: CustomerOrder, request_hash: str) -> CustomerOrder:
    if order.request_hash != request_hash:
        raise HTTPException(409, "This submission reference has already been used.")
    return order


@router.post("/api/orders", response_model=Receipt, status_code=201)
def submit_order(data: OrderRequest, db: Database, response: Response):
    response.headers["Cache-Control"] = "no-store"
    reference = str(data.reference)
    request_hash = sha256(data.model_dump_json().encode()).hexdigest()
    existing = db.get(CustomerOrder, reference)
    if existing is not None:
        return receipt_view(db, match_request(existing, request_hash))

    settings = db.get_one(OrderSettings, 1, with_for_update=True)
    existing = db.get(CustomerOrder, reference)
    if existing is not None:
        return receipt_view(db, match_request(existing, request_hash))
    if settings.daily_limit is not None and requests_today(db) >= settings.daily_limit:
        raise HTTPException(409, "Today's order request limit has been reached.")

    menu = db.scalars(
        select(MenuEntry).where(MenuEntry.id.in_([line.menu_id for line in data.lines])).with_for_update(read=True)
    )
    entries = {entry.id: entry for entry in menu}
    lines = []
    for line in data.lines:
        entry = entries.get(line.menu_id)
        if entry is None or not entry.available or entry.starting_at or entry.max_price_ngwee is not None:
            raise HTTPException(409, "An item needs a quote or is no longer available. Review the menu.")
        if entry.price_ngwee != line.expected_price_ngwee:
            raise HTTPException(409, "An item price changed. Review the menu before submitting.")
        lines.append(dict(name=entry.name, option=entry.option, quantity=line.quantity,
                          unit_price_ngwee=entry.price_ngwee))

    total = sum(line["quantity"] * line["unit_price_ngwee"] for line in lines)
    db.execute(insert(CustomerOrder).values(
        reference=reference,
        request_hash=request_hash,
        customer_name=data.customer_name,
        phone=data.phone,
        fulfillment=data.fulfillment,
        address=data.address if data.fulfillment == "delivery" else "",
        items=lines,
        total_ngwee=total,
    ).on_conflict_do_nothing(index_elements=[CustomerOrder.reference]))
    order = db.get_one(CustomerOrder, reference)
    match_request(order, request_hash)
    db.commit()
    return order


@router.get("/api/orders/{reference}", response_model=Receipt)
def get_receipt(reference: UUID, db: Database, response: Response):
    response.headers["Cache-Control"] = "no-store"
    order = db.get(CustomerOrder, str(reference))
    if order is None:
        raise HTTPException(404, "Order reference not found.")
    return receipt_view(db, order)


def receipt_view(db: Database, order: CustomerOrder) -> Receipt:
    return Receipt.model_validate(order).model_copy(update={"paid_ngwee": paid_total(db, "orders", order.reference)})


@owner.get("/owner/api/orders", response_model=list[OwnerOrder])
def recent_orders(db: Database, response: Response):
    response.headers.update(PRIVATE)
    rows = db.scalars(select(CustomerOrder).order_by(CustomerOrder.created_at.desc()).limit(50))
    return [owner_view(db, row) for row in rows]


def requests_today(db: Database) -> int:
    start = datetime.now(KITWE).replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(select(func.count()).select_from(CustomerOrder).where(
        CustomerOrder.created_at >= start, CustomerOrder.created_at < start + timedelta(days=1)
    )) or 0


class Capacity(BaseModel):
    daily_limit: int | None = Field(ge=1, le=10000, strict=True)


class CapacityView(Capacity):
    requests_today: int


@owner.get("/owner/api/capacity", response_model=CapacityView)
def owner_capacity(db: Database, response: Response):
    response.headers.update(PRIVATE)
    return CapacityView(daily_limit=db.get_one(OrderSettings, 1).daily_limit, requests_today=requests_today(db))


@owner.put("/owner/api/capacity", response_model=CapacityView, dependencies=[WriteRequest])
def set_capacity(data: Capacity, db: Database, response: Response):
    db.get_one(OrderSettings, 1, with_for_update=True).daily_limit = data.daily_limit
    db.commit()
    return owner_capacity(db, response)


class StatusChange(BaseModel):
    status: Status


def transition(db: Database, reference: UUID, target: Status, actor: str) -> CustomerOrder:
    order = db.get(CustomerOrder, str(reference), with_for_update=True)
    if order is None:
        raise HTTPException(404, "Order not found.", headers=PRIVATE)
    allowed = KITCHEN_STEPS if actor == "kitchen" else NEXT
    if target not in allowed.get(order.status, ()):
        raise HTTPException(409, "That change is unavailable. Refresh the order list.", headers=PRIVATE)
    order.status = target
    db.add(OrderStatusEvent(reference=order.reference, actor=actor, status=target))
    db.commit()
    return order


@owner.put("/owner/api/orders/{reference}/status", response_model=OwnerOrder, dependencies=[WriteRequest])
def owner_status(reference: UUID, data: StatusChange, db: Database, response: Response):
    response.headers.update(PRIVATE)
    return owner_view(db, transition(db, reference, data.status, "owner"))


def owner_view(db: Database, order: CustomerOrder) -> OwnerOrder:
    return OwnerOrder.model_validate(order).model_copy(
        update={"paid_ngwee": paid_total(db, "orders", order.reference)}
    )


class KitchenLine(BaseModel):
    name: str
    option: str
    quantity: int


class KitchenOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    status: Status
    fulfillment: Literal["pickup", "delivery"]
    items: list[KitchenLine]
    created_at: datetime


@kitchen.get("/kitchen", response_class=FileResponse)
def kitchen_page():
    return FileResponse(KITCHEN_FILES / "index.html", headers={**PRIVATE, "Content-Security-Policy": CSP})


@kitchen.get("/kitchen/assets/{filename}", response_class=FileResponse)
def kitchen_asset(filename: str):
    paths = {"board.js": KITCHEN_FILES / "board.js",
             "board.css": KITCHEN_FILES.parent / "owner" / "dashboard.css"}
    if filename not in paths:
        raise HTTPException(404, headers=PRIVATE)
    return FileResponse(paths[filename], headers={**PRIVATE, "X-Content-Type-Options": "nosniff"})


@kitchen.get("/kitchen/api/orders", response_model=list[KitchenOrder])
def kitchen_orders(db: Database, response: Response):
    response.headers.update(PRIVATE)
    return db.scalars(select(CustomerOrder).where(
        CustomerOrder.status.in_(("confirmed", "preparing", "ready"))
    ).order_by(CustomerOrder.created_at, CustomerOrder.reference)).all()


@kitchen.put("/kitchen/api/orders/{reference}/status", response_model=KitchenOrder, dependencies=[WriteRequest])
def kitchen_status(reference: UUID, data: StatusChange, db: Database, response: Response):
    response.headers.update(PRIVATE)
    return transition(db, reference, data.status, "kitchen")
