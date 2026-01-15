from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from typing import Optional

from backend.app.database import get_db
from backend.app.crud.fighters import get_all_fighters
from backend.app.crud.events import get_all_events
from backend.app.crud.fights import get_fights

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
def search_page(
    request: Request,
    db: Session = Depends(get_db),
    q: Optional[str] = None
):
    """
    Renders the search page with optional query `q`.
    Can search fighters, events, and fights.
    """
    fighters, events, fights_list = [], [], []

    if q:
        q_lower = q.lower()
        # Filter fighters
        fighters = [f for f in get_all_fighters(db) if q_lower in f.name.lower()]
        # Filter events
        events = [e for e in get_all_events(db) if q_lower in e.name.lower()]
        # Filter fights by fighter names
        fights_list = [
            f for f in get_fights(db, skip=0, limit=100)
            if q_lower in f.fighter1.name.lower() or q_lower in f.fighter2.name.lower()
        ]

    return templates.TemplateResponse(
        "search/index.html",
        {
            "request": request,
            "query": q,
            "fighters": fighters,
            "events": events,
            "fights": fights_list,
        }
    )
