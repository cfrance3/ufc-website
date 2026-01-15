from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.app.routers import fighters, events, fights, search, home


app = FastAPI(title="UFC Database API")

templates = Jinja2Templates(directory="frontend/templates")

app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)

app.include_router(home.router)
app.include_router(fighters.router)
app.include_router(fights.router)
app.include_router(events.router)
app.include_router(search.router)
