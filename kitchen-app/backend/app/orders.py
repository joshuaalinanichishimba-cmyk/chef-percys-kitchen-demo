from datetime import datetime
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .menu import Database, PRIVATE, owner
from .models import CustomerOrder, MenuEntry

router = APIRouter()


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
    status: Literal["received"] = "received"


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
        return match_request(existing, request_hash)

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
    return order


@owner.get("/owner/api/orders", response_model=list[OwnerOrder])
def recent_orders(db: Database, response: Response):
    response.headers.update(PRIVATE)
    return db.scalars(select(CustomerOrder).order_by(CustomerOrder.created_at.desc()).limit(50)).all()
