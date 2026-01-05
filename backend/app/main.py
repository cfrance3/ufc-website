from fastapi import FastAPI
from backend.app.routers import fighters

app = FastAPI(title="UFC Database API")

app.include_router(fighters.router)

@app.get("/")
def root():
    return {"status": "UFC API running"}
