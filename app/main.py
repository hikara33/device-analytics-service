from fastapi import FastAPI

from app.db.database import Base, engine
from app.models import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Device Analytics Service")

@app.get("/")
def root():
  return { "status": "ok" }