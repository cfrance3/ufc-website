from fastapi import FastAPI
from backend.app.routers import fighters, events, fights

app = FastAPI(title="UFC Database API")

app.include_router(fighters.router)
app.include_router(events.router)
app.include_router(fights.router)

@app.get("/")
def root():
    return {"status": "UFC API running"}
