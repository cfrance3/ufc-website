from sqlalchemy.orm import Session
from backend.app.models import Fight

def get_all_fights(db: Session):
    return db.query(Fight).all()

def insert_fight(db: Session, fight_data: dict):
    fight = Fight(**fight_data)
    db.add(fight)
    db.commit()
    db.refresh(fight)
    return fight