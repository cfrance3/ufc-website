from sqlalchemy.orm import Session
from backend.app.models import Event

def get_all_events(db: Session):
    return db.query(Event).all()

def insert_event(db: Session, event_data: dict):
    event = Event(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def upsert_event(db: Session, event_data: dict):
    event = db.query(Event).filter(Event.name == event_data["name"]).first()
    if event:
        for key, value in event_data.items():
            setattr(event, key, value)
    else:
        event = Event(**event_data)
        db.add(event)
    db.commit()
    db.refresh(event)
    return event