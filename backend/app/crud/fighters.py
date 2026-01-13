from typing import List
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.app.models import Fighter, Event, Fight
from backend.app.crud.utils import apply_updates

def get_all_fighters(db: Session) -> List[Fighter]:
    return db.query(Fighter).filter(Fighter.is_deleted.is_(False)).all()

def insert_fighter(db: Session, fighter_data: dict) -> Fighter:
    fighter = Fighter(**fighter_data)
    db.add(fighter)
    return fighter

# Inserts fighter if not present, updates otherwise.
#  DOES NOT SUPPORT RESTORE
def upsert_fighter(db: Session, fighter_data: dict) -> Fighter:
    fighter = db.query(Fighter).filter(Fighter.url == fighter_data["url"]).first()
    if fighter:
        if fighter.is_deleted:
            return fighter
        apply_updates(fighter, fighter_data)
    else:
        fighter = Fighter(**fighter_data)
        db.add(fighter)
    return fighter

# Inserts fighter if not present, updates otherwise. Restores fighter if marked delted. 
# USED ONLY FOR IMPORTS
def upsert_fighter_from_import(db: Session, fighter_data: dict) -> Fighter:
    fighter = db.query(Fighter).filter(Fighter.url == fighter_data["url"]).first()
    if fighter:
        apply_updates(fighter, fighter_data)
        fighter.is_deleted = False
    else:
        fighter = Fighter(**fighter_data)
        db.add(fighter)

    return fighter

def soft_delete_fighter(db: Session, fighter_id: int) -> bool:
    fighter = db.get(Fighter, fighter_id)
    if not fighter or fighter.is_deleted:
        return False
    
    fighter.is_deleted = True

    return True

def update_fighter(db: Session, fighter_id: int, fighter_data: dict, *, restore: bool = False) -> Fighter | None:
    fighter = db.get(Fighter, fighter_id)
    if not fighter:
        return None
    
    if fighter.is_deleted and not restore:
        return None
    
    apply_updates(fighter, fighter_data)

    if restore:
        fighter.is_deleted = False

    return fighter

def get_fighter_by_url(db: Session, fighter_url: str) -> Fighter | None:
    return db.query(Fighter).filter(Fighter.url == fighter_url, Fighter.is_deleted.is_(False)).first()

def get_fighter_by_name_and_event(db: Session, fighter_name: str, event_name: str) -> List[Fighter] | None:
    return (
        db.query(Fighter)
        .join(Fight,
              or_(
                  Fight.fighter1_id == Fighter.id,
                  Fight.fighter2_id == Fighter.id
              )
        )
        .join(Event, Fight.event_id == Event.id)
        .filter(
            Fighter.name == fighter_name,
            Event.name == event_name,
            Fighter.is_deleted.is_(False),
            Fight.is_deleted.is_(False)
        )
        .distinct()
        .all()
    )