from fastapi import FastAPI
from app.api.routes import router
from app.db.init_db import init_db

app = FastAPI(title="Device Analytics Service")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok"}

app.include_router(router)