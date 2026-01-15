import random
from typing import List
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload
from backend.app.models import Fight, Event, Fighter
from backend.app.crud.utils import apply_updates
from backend.app.constants import WEIGHTCLASS_TO_WEIGHT

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

def get_fight_by_event_and_fighters(db: Session, event_id: int, fighter1_id: int, fighter2_id: int) -> Fight | None:
    return (
        db.query(Fight)
        .filter(
            Fight.event_id == event_id,
            Fight.is_deleted.is_(False),
            (
                (Fight.fighter1_id == fighter1_id) &
                (Fight.fighter2_id == fighter2_id)
            ) |
            (
                (Fight.fighter1_id == fighter2_id) &
                (Fight.fighter2_id == fighter1_id)
            )
        )
        .first()
    )

def fighter_fought_opponent_at_event(db: Session, *, fighter_url: str, opponent_urls: list[str], event_name: str) -> bool:
    if not opponent_urls:
        return False
    
    return (
        db.query(Fight.id)
        .join(Event, Fight.event_id == Event.id)
        .filter(
            Event.name == event_name,
            Fight.is_deleted.is_(False),
            or_(
                and_(Fight.fighter1.has(Fighter.url == fighter_url),
                     Fight.fighter2.has(Fighter.url.in_(opponent_urls)),
                     ),
                     and_(
                         Fighter.fighter2.has(Fighter.url == fighter_url),
                         Fight.fighter1.has(Fighter.url.in_(opponent_urls)),
                     ),
            ),
        )
        .first()
        is not None
    )

def get_fight_count(db: Session) -> int:
    return db.query(Fight).count()

def get_fight_by_offset(db: Session, offset: int):
    return (
        db.query(Fight)
        .options(
            joinedload(Fight.fighter1),
            joinedload(Fight.fighter2),
            joinedload(Fight.event)
        )
        .offset(offset)
        .limit(1)
        .one_or_none()
    )

def get_random_fight(db: Session, seed: int | None = None):
    count = get_fight_count(db)
    if count == 0:
        return None
    
    rng = random.Random(seed)
    offset = rng.randrange(count)

    return get_fight_by_offset(db, offset)

def get_fight_display_data(fight: Fight):
    weight = WEIGHTCLASS_TO_WEIGHT.get(fight.weightclass, "N/A")

    return {
        "fighter1": {
            "name": fight.fighter1.name,
            "record": fight.fighter1.record,
            "height": fight.fighter1.height,
            "weight": weight,
            "stance": fight.fighter1.stance,
        },
        "fighter2": {
            "name": fight.fighter2.name,
            "record": fight.fighter2.record,
            "height": fight.fighter2.height,
            "weight": weight,
            "stance": fight.fighter2.stance,
        },
        "weightclass": fight.weightclass,
        "method": fight.method,
        "round": fight.round,
        "time": fight.time,
        "title_status": fight.title_status,
    }

def get_fight_by_id(db: Session, id: int) -> Fight | None:
    return db.query(Fight).filter(Fight.id == id).one_or_none()