from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from backend.app.database import get_db
from backend.app.crud.events import get_all_events
from backend.app.schemas import Event as EventSchema
from typing import List, Optional

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter(prefix="/events", tags=["events"])

@router.get("/api", response_model=List[EventSchema])
def api_list_events(db: Session = Depends(get_db)):
    return get_all_events(db)

@router.get("/")
def events_page(request: Request, db: Session = Depends(get_db), q: Optional[str] = None):
    """
    renders events page template
    Optional query 'q' can be used for search/filtering
    """

    events = get_all_events(db)

    if q:
        events = [e for e in events if (q.lower() in e.name.lower())]

    return templates.TemplateResponse(
        "events/list.html",
        {"request": request, "events": events, "query": q}
    )