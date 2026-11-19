from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_engine
from .models import MenuEntry
from .owner_auth import require_owner

router = APIRouter()
owner = APIRouter(dependencies=[Depends(require_owner)], include_in_schema=False)
OWNER_FILES = Path(__file__).with_name("owner")
PRIVATE = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"


class MenuFields(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid", str_strip_whitespace=True)

    category: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    name: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    option: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=400)
    price_ngwee: int = Field(gt=0, le=100_000_000, strict=True)
    max_price_ngwee: int | None = Field(default=None, gt=0, le=100_000_000, strict=True)
    starting_at: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def validate_price(self):
        if self.max_price_ngwee is not None and (self.starting_at or self.max_price_ngwee <= self.price_ngwee):
            raise ValueError("A price range needs a higher maximum and cannot also be a starting price.")
        return self


class PublicEntry(MenuFields):
    id: int


class OwnerFields(MenuFields):
    available: bool = Field(strict=True)


class OwnerEntry(OwnerFields):
    id: int


def session_scope():
    with Session(get_engine()) as session:
        yield session


Database = Annotated[Session, Depends(session_scope)]


@router.get("/api/menu", response_model=list[PublicEntry])
def public_menu(db: Database, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return db.scalars(select(MenuEntry).where(MenuEntry.available.is_(True)).order_by(MenuEntry.id)).all()


@owner.get("/owner", response_class=FileResponse)
def owner_dashboard():
    return FileResponse(OWNER_FILES / "index.html", headers={**PRIVATE, "Content-Security-Policy": CSP})


@owner.get("/owner/assets/{filename}", response_class=FileResponse)
def owner_assets(filename: str):
    if filename not in {"dashboard.js", "dashboard.css", "bookings.js"}:
        raise HTTPException(404)
    return FileResponse(OWNER_FILES / filename, headers={**PRIVATE, "X-Content-Type-Options": "nosniff"})


@owner.get("/owner/api/menu", response_model=list[OwnerEntry])
def owner_menu(db: Database, response: Response):
    response.headers.update(PRIVATE)
    return db.scalars(select(MenuEntry).order_by(MenuEntry.id)).all()


def require_dashboard_request(x_owner_action: Annotated[str | None, Header()] = None):
    if x_owner_action != "menu-edit":
        raise HTTPException(403, "Missing dashboard request header.", headers=PRIVATE)


WriteRequest = Depends(require_dashboard_request)


@owner.post("/owner/api/menu", status_code=201, response_model=OwnerEntry, dependencies=[WriteRequest])
def add_entry(data: OwnerFields, db: Database, response: Response):
    entry = MenuEntry(**data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    response.headers.update(PRIVATE)
    return entry


@owner.put("/owner/api/menu/{entry_id}", response_model=OwnerEntry, dependencies=[WriteRequest])
def edit_entry(entry_id: int, data: OwnerFields, db: Database, response: Response):
    entry = db.get(MenuEntry, entry_id)
    if entry is None:
        raise HTTPException(404, "Menu entry not found.", headers=PRIVATE)
    for field, value in data.model_dump().items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    response.headers.update(PRIVATE)
    return entry
