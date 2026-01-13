from typing import List
from sqlalchemy.orm import Session
from backend.app.models import Event
from backend.app.crud.utils import apply_updates

def get_all_events(db: Session) -> List[Event]:
    return db.query(Event).filter(Event.is_deleted.is_(False)).all()

def insert_event(db: Session, event_data: dict) -> Event:
    event = Event(**event_data)
    db.add(event)
    return event

# Inserts event if not present, updates otherwise.
# DOES NOT SUPPORT RESTORE
def upsert_event(db: Session, event_data: dict) -> Event:
    event = db.query(Event).filter(Event.name == event_data["name"]).first()
    if event:
        if event.is_deleted:
            return event
        apply_updates(event, event_data)
    else:
        event = Event(**event_data)
        db.add(event)
    return event

# Inserts fighter if not present, updates otherwise. Restores fighter if marked delted. 
# USED ONLY FOR IMPORTS
def upsert_event_from_import(db: Session, event_data: dict) -> Event:
    event = db.query(Event).filter(Event.name == event_data["name"]).first()
    if event:
        apply_updates(event, event_data)
        event.is_deleted = False
    else:
        event = Event(**event_data)
        db.add(event)
    return event

def soft_delete_event(db: Session, event_id: int) -> bool:
    event = db.get(Event, event_id)
    if not event or event.is_deleted:
        return False
    
    event.is_deleted = True
    return True

def update_event(db: Session, event_id: int, event_data: dict, *, restore: bool = False) -> Event | None:
    event = db.get(Event, event_id)
    if not event:
        return None
    if event.is_deleted and not restore:
        return None
    
    apply_updates(event, event_data)

    if restore:
        event.is_deleted = False

    return event
    
def get_event_by_name(db: Session, event_name: str) -> Event | None:
    return (
        db.query(Event)
        .filter(Event.name == event_name)
        .first()
    )
    