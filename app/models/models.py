from app.db.database import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime

class DeviceData(Base):
  __tablename__ = "device_data"

  id = Column(Integer, primary_key=True, index=True)
  device_id = Column(String, index=True)

  x = Column(Float)
  y = Column(Float)
  z = Column(Float)

  timestamp = Column(DateTime(timezone=True), default=lambda:
                     datetime.now(timezone.utc))