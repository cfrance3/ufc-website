from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.crud.fighters import get_all_fighters
from backend.app.schemas import Fighter as FighterSchema
from typing import List

router = APIRouter(prefix="/fighters", tags=["fighters"])

@router.get("/", response_model=List[FighterSchema])
def list_fighters(db: Session = Depends(get_db)):
    return get_all_fighters(db)