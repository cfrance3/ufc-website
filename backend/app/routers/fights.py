from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.crud.fights import get_fights
from backend.app.schemas import Fight as FightSchema
from typing import List

router = APIRouter(prefix="/fights", tags=["fights"])

@router.get("/", response_model=List[FightSchema])
def list_fights(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return get_fights(db, skip, limit)