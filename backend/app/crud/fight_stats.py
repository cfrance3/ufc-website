from typing import List
from sqlalchemy.orm import Session
from backend.app.models import FightStats, Fight

def get_all_fight_stats(db: Session) -> List[FightStats]:
    return db.query(FightStats).join(FightStats.fight).filter(Fight.is_deleted.is_(False)).all()

def insert_fight_stats(db: Session, fightStats_data: dict) -> FightStats:
    fightStats = FightStats(**fightStats_data)
    db.add(fightStats)
    return fightStats

def delete_fight_stats(db: Session, fightStats_id) -> bool:
    fightStats = db.get(FightStats, fightStats_id)
    if not fightStats:
        return False
    db.delete(fightStats)
