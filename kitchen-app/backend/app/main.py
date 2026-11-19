from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import get_engine
from .menu import owner, router as menu
from .models import BusinessProfile
from .orders import router as orders

app = FastAPI(title="Chèf Percy’s Kitchen API", version="0.1.0")


class PublicBusinessProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    contact_name: str
    location: str
    airtel: str
    mtn: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/ready")
def ready() -> dict[str, str]:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1 FROM business_profile WHERE id = 1")).scalar_one()
    except (RuntimeError, SQLAlchemyError) as error:
        raise HTTPException(503, "Database is not ready.") from error
    return {"status": "ready"}


@app.get("/api/business", response_model=PublicBusinessProfile)
def business() -> PublicBusinessProfile:
    try:
        with Session(get_engine()) as session:
            profile = session.get(BusinessProfile, 1)
            if profile is None:
                raise HTTPException(503, "Business profile is unavailable.")
            return PublicBusinessProfile.model_validate(profile)
    except (RuntimeError, SQLAlchemyError) as error:
        raise HTTPException(503, "Database is not ready.") from error


app.include_router(menu)
app.include_router(orders)
app.include_router(owner)

dist = Path(__file__).resolve().parents[2] / "dist"
if dist.is_dir():
    app.mount("/", StaticFiles(directory=dist, html=True), name="customer")
