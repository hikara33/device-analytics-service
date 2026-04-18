from fastapi import FastAPI

app = FastAPI(title="Device Analytics Service")

@app.get("/")
def root():
  return { "status": "ok" }