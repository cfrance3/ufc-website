from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.crud.fights import get_all_fights
from backend.app.schemas import Fight as FightSchema
from typing import List

router = APIRouter(prefix="/fights", tags=["fights"])

@router.get("/", response_model=List[FightSchema])
def list_fights(db: Session = Depends(get_db)):
    return get_all_fights(db)