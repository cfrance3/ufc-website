from typing import List
from sqlalchemy.orm import Session
from backend.app.models import FightStats, Fight

def get_all_fight_stats(db: Session) -> List[FightStats]:
    return db.query(FightStats).join(FightStats.fight).filter(Fight.is_deleted.is_(False)).all()

def insert_fight_stats(db: Session, fight_stats_data: dict) -> FightStats:
    fight_stats = FightStats(**fight_stats_data)
    db.add(fight_stats)
    return fight_stats

def delete_fight_stats(db: Session, fight_stats_id) -> bool:
    fight_stats = db.get(FightStats, fight_stats_id)
    if not fight_stats:
        return False
    db.delete(fight_stats)

def get_fight_stats(db: Session, fight_id: int, fighter_id: int) -> FightStats | None:
    return (db.query(FightStats)
        .join(Fight)
        .filter(
        FightStats.fight_id == fight_id, 
        FightStats.fighter_id == fighter_id,
        Fight.is_deleted.is_(False)
        ).first()
    )

def get_or_create_fight_stats(db: Session, fight_id: int, fighter_id: int) -> FightStats:
    for obj in db.new:
        if isinstance(obj, FightStats) and obj.fight_id == fight_id and obj.fighter_id == fighter_id:
            return obj
        
    fight_stats = (
        db.query(FightStats)
        .join(Fight)
        .filter(
            FightStats.fight_id == fight_id,
            FightStats.fighter_id == fighter_id,
            Fight.is_deleted.is_(False)
        )
        .first()
    )

    if fight_stats:
        return fight_stats
    
    fight_stats = FightStats(fight_id=fight_id, fighter_id=fighter_id)
    db.add(fight_stats)
    return fight_stats

