from typing import List
from sqlalchemy.orm import Session, joinedload
from backend.app.models import Fight
from utils import apply_updates

def get_all_fights(db: Session) -> List[Fight]:
    return db.query(Fight).filter(Fight.is_deleted.is_(False)).all()

def insert_fight(db: Session, fight_data: dict) -> Fight:
    fight = Fight(**fight_data)
    db.add(fight)
    return fight

def get_fights(db: Session, skip: int = 0, limit: int = 100) -> List[Fight]:
    return (
        db.query(Fight)
        .options(
            joinedload(Fight.fighter1),
            joinedload(Fight.fighter2),
            joinedload(Fight.event)
        )
        .filter(Fight.is_deleted.is_(False))
        .offset(skip)
        .limit(limit)
        .all()
    )

def soft_delete_fight(db: Session, fight_id: int) -> bool:
    fight = db.get(Fight, fight_id)
    if not fight or fight.is_deleted:
        return False
    
    fight.is_deleted = True
    return True

def update_fight(db: Session, fight_id: int, fight_data: dict, *, restore: bool = False) -> Fight | None:
    fight = db.get(Fight, fight_id)
    if not fight:
        return None
    
    if fight.is_deleted and not restore:
        return None
    
    apply_updates(fight, fight_data)

    if restore:
        fight.is_deleted = False

    return fight