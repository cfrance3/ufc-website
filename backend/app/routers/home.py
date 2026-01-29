from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.crud.fights import get_random_fight, get_fight_display_data, get_fight_by_id

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()

@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    # seed = date.today().toordinal()
    seed = None

    fight_of_the_day = get_random_fight(db, seed)
    fight_display = get_fight_display_data(fight_of_the_day)

    return templates.TemplateResponse(
        "index.html",
        {"request": request,
         "fight_of_the_day": fight_display
         }
    )