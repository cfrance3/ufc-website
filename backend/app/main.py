from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.app.routers import fighters, events, fights, search


app = FastAPI(title="UFC Database API")

templates = Jinja2Templates(directory="frontend/templates")

app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)

app.include_router(fighters.router)
app.include_router(events.router)
app.include_router(fights.router)

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/search")
def search(request: Request, q: str = None):
    return templates.TemplateResponse(
        "search/index.html",
        {"request": request, "query": q}
    )

@app.get("/fights")
def fights(request: Request, q: str = None):
    return templates.TemplateResponse(
        "fights/list.html",
        {"request": request, "query": q}
    )

@app.get("/fighters")
def fights(request: Request, q: str = None):
    return templates.TemplateResponse(
        "fighters/list.html",
        {"request": request, "query": q}
    )

@app.get("/events")
def fights(request: Request, q: str = None):
    return templates.TemplateResponse(
        "events/list.html",
        {"request": request, "query": q}
    )
