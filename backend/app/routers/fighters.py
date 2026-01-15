from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from typing import List, Optional

from backend.app.database import get_db
from backend.app.crud.fighters import get_all_fighters
from backend.app.schemas import Fighter as FighterSchema

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter(prefix="/fighters", tags=["fighters"])

@router.get("/api", response_model=List[FighterSchema])
def api_list_fighters(db: Session = Depends(get_db)):
    return get_all_fighters(db)

@router.get("/")
def fighters_page(request: Request, db: Session = Depends(get_db), q: Optional[str] = None):
    """
    Renders fighters page template
    Optional query 'q' can be used for searching/filtering
    """

    fighters = get_all_fighters(db)

    if q:
        fighters = [f for f in fighters if q.lower() in f.name.lower()]

    return templates.TemplateResponse(
        "fighters/list.html",
        {"request": request, "fighters": fighters, "query": q}
    )