from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from typing import List, Optional

from backend.app.database import get_db
from backend.app.crud.fights import get_fights
from backend.app.schemas import Fight as FightSchema

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter(prefix="/fights", tags=["fights"])


@router.get("/api", response_model=List[FightSchema])
def list_fights(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_fights(db, skip, limit)

@router.get("/")
def fights_page(
    request: Request,
    db: Session = Depends(get_db),
    q: Optional[str] = None
):
    """
    Renders fights page template.
    Optional search query `q` can filter by fighter name.
    """
    fights = get_fights(db, skip=0, limit=100)  # default for page

    if q:
        # Filter fights where either fighter1 or fighter2 name contains q
        fights = [
            f for f in fights
            if q.lower() in f.fighter1.name.lower() or q.lower() in f.fighter2.name.lower()
        ]

    return templates.TemplateResponse(
        "fights/list.html",
        {"request": request, "fights": fights, "query": q}
    )
