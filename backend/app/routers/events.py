from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.crud.events import get_all_events
from backend.app.schemas import Event as EventSchema
from typing import List

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[EventSchema])
def list_events(db: Session = Depends(get_db)):
    return get_all_events(db)