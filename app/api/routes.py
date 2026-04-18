from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import DeviceData
from app.schemas.schemas import DeviceDataCreate

router = APIRouter()


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
     db.close()


@router.post("/data")
def create_data(data: DeviceDataCreate, db: Session = Depends(get_db)):
  record = DeviceData(**data.dict())
  db.add(record)
  db.commit()
  db.refresh(record)
  return record