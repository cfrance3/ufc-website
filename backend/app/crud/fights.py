from sqlalchemy.orm import Session, joinedload
from backend.app.models import Fight

def get_all_fights(db: Session):
    return db.query(Fight).all()

def insert_fight(db: Session, fight_data: dict):
    fight = Fight(**fight_data)
    db.add(fight)
    db.commit()
    db.refresh(fight)
    return fight

def get_fights(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Fight)
        .options(
            joinedload(Fight.fighter1),
            joinedload(Fight.fighter2),
            joinedload(Fight.event)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )