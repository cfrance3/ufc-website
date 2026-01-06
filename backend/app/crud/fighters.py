from sqlalchemy.orm import Session
from backend.app.models import Fighter

def get_all_fighters(db: Session):
    return db.query(Fighter).all()

def upsert_fighter(db: Session, fighter_data: dict):
    fighter = db.query(Fighter).filter(Fighter.name == fighter_data["name"]).first()
    if fighter:
        for key, value in fighter_data.items():
            setattr(fighter, key, value)
    else:
        fighter = Fighter(**fighter_data)
        db.add(fighter)
    db.commit()
    db.refresh(fighter)
    return fighter