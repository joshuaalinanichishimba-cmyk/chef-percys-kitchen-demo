from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from .bookings import PaymentInput
from .database import get_engine
from .menu import Database, PRIVATE, WriteRequest, owner
from .models import DigitalProduct, DigitalPurchase, VerifiedPayment
from sqlalchemy.orm import Session

router = APIRouter()
MAX_PDF = 10 * 1024 * 1024
DOWNLOAD_HEADERS = {**PRIVATE, "X-Content-Type-Options": "nosniff",
                    "Content-Security-Policy": "sandbox", "Content-Disposition": "attachment; filename=chef-percy.pdf"}


class ProductInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=800)
    kind: Literal["recipe", "cookbook"]
    price_ngwee: int = Field(gt=0, le=100_000_000, strict=True)


class ProductView(ProductInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OwnerProduct(ProductView):
    published: bool
    has_pdf: bool


def product(row_id: int, db: Database, lock: bool = False) -> DigitalProduct:
    item = db.get(DigitalProduct, row_id, with_for_update=lock)
    if item is None:
        raise HTTPException(404, "Product not found.", headers=PRIVATE)
    return item


def owner_product(item: DigitalProduct, has_pdf: bool) -> OwnerProduct:
    return OwnerProduct(**ProductView.model_validate(item).model_dump(),
                        published=item.published, has_pdf=has_pdf)


@router.get("/api/digital", response_model=list[ProductView])
def catalogue(db: Database):
    return db.scalars(select(DigitalProduct).where(DigitalProduct.published.is_(True)).order_by(DigitalProduct.id)).all()


@owner.get("/owner/api/digital", response_model=list[OwnerProduct])
def owner_catalogue(db: Database, response: Response):
    response.headers.update(PRIVATE)
    return [owner_product(item, has_pdf) for item, has_pdf in db.execute(
        select(DigitalProduct, DigitalProduct.pdf.is_not(None)).order_by(DigitalProduct.id)
    )]


@owner.post("/owner/api/digital", response_model=OwnerProduct, status_code=201, dependencies=[WriteRequest])
def create_product(data: ProductInput, db: Database, response: Response):
    item = DigitalProduct(**data.model_dump(), published=False)
    db.add(item)
    db.commit()
    response.headers.update(PRIVATE)
    return owner_product(item, False)


@owner.put("/owner/api/digital/{item_id}", response_model=OwnerProduct, dependencies=[WriteRequest])
def update_product(item_id: int, data: ProductInput, db: Database, response: Response):
    item = product(item_id, db, lock=True)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    response.headers.update(PRIVATE)
    return owner_product(item, item.pdf is not None)


def save_pdf(item_id: int, content: bytes) -> None:
    with Session(get_engine()) as db:
        item = product(item_id, db, lock=True)
        if item.published or db.scalar(select(DigitalPurchase.reference).where(
            DigitalPurchase.product_id == item_id
        ).limit(1)):
            raise HTTPException(409, "Upload a replacement to a new draft once a product has been sold.", headers=PRIVATE)
        item.pdf = content
        db.commit()


@owner.put("/owner/api/digital/{item_id}/pdf", status_code=204, dependencies=[WriteRequest])
async def upload_pdf(item_id: int, request: Request):
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_PDF:
            raise HTTPException(413, "The PDF must be 10 MB or smaller.", headers=PRIVATE)
        content.extend(chunk)
    if not content.startswith(b"%PDF-"):
        raise HTTPException(422, "Choose a PDF file.", headers=PRIVATE)
    await run_in_threadpool(save_pdf, item_id, bytes(content))
    return Response(status_code=204, headers=PRIVATE)


class Publication(BaseModel):
    published: bool = Field(strict=True)


@owner.put("/owner/api/digital/{item_id}/publication", response_model=OwnerProduct, dependencies=[WriteRequest])
def publish_product(item_id: int, data: Publication, db: Database, response: Response):
    item = product(item_id, db, lock=True)
    has_pdf = item.pdf is not None
    if data.published and not has_pdf:
        raise HTTPException(409, "Upload a PDF before publishing.", headers=PRIVATE)
    item.published = data.published
    db.commit()
    response.headers.update(PRIVATE)
    return owner_product(item, has_pdf)


class DownloadCode(BaseModel):
    token: str = Field(pattern=r"^[a-f0-9]{64}$")


class Sale(PaymentInput, DownloadCode):
    replace_code: bool = Field(default=False, strict=True)


class SaleView(BaseModel):
    reference: str
    expires_at: datetime


@owner.post("/owner/api/digital/{item_id}/sales", response_model=SaleView, status_code=201, dependencies=[WriteRequest])
def record_sale(item_id: int, data: Sale, db: Database, response: Response):
    item = product(item_id, db, lock=True)
    token_hash = sha256(data.token.encode()).hexdigest()
    transaction = data.transaction_reference.upper()
    existing = db.scalar(select(VerifiedPayment).where(
        VerifiedPayment.channel == data.channel, VerifiedPayment.transaction_reference == transaction
    ))
    if existing is not None:
        purchase = db.get(DigitalPurchase, existing.digital_reference) if existing.digital_reference else None
        if purchase is None or purchase.product_id != item_id or existing.amount_ngwee != data.amount_ngwee:
            raise HTTPException(409, "This transaction reference was already recorded.", headers=PRIVATE)
        if purchase.token_hash != token_hash:
            if not data.replace_code:
                raise HTTPException(409, "This sale already has a code. Use Replace download code.", headers=PRIVATE)
            purchase.token_hash = token_hash
            purchase.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            try:
                db.commit()
            except IntegrityError as error:
                db.rollback()
                raise HTTPException(409, "Choose a different download code.", headers=PRIVATE) from error
    else:
        if data.replace_code:
            raise HTTPException(404, "No recorded digital sale matches that transaction.", headers=PRIVATE)
        if not item.published or data.amount_ngwee != item.price_ngwee:
            raise HTTPException(409, "A sale requires a published product and its full listed price.", headers=PRIVATE)
        purchase = DigitalPurchase(reference=str(uuid4()), product_id=item_id, token_hash=token_hash,
                                  expires_at=datetime.now(timezone.utc) + timedelta(days=7))
        db.add(purchase)
        try:
            db.flush()
            db.add(VerifiedPayment(digital_reference=purchase.reference, channel=data.channel,
                                   transaction_reference=transaction, amount_ngwee=data.amount_ngwee))
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise HTTPException(409, "This payment reference or download code was already used.", headers=PRIVATE) from error
    response.headers.update(PRIVATE)
    return SaleView(reference=purchase.reference, expires_at=purchase.expires_at)


@router.post("/api/digital/download", response_class=Response)
def download(data: DownloadCode, db: Database):
    token_hash = sha256(data.token.encode()).hexdigest()
    content = db.scalar(select(DigitalProduct.pdf).join(
        DigitalPurchase, DigitalPurchase.product_id == DigitalProduct.id
    ).where(DigitalPurchase.token_hash == token_hash, DigitalPurchase.expires_at > datetime.now(timezone.utc)))
    if content is None:
        raise HTTPException(404, "Download code not found or expired.", headers=PRIVATE)
    return Response(content, media_type="application/pdf", headers=DOWNLOAD_HEADERS)
