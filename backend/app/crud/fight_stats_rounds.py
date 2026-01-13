from typing import List
from sqlalchemy.orm import Session
from backend.app.models import FightStatsRound, FightStats, Fight

def get_all_fight_stats_round(db: Session) -> List[FightStatsRound]:
    return db.query(FightStatsRound).join(FightStats).join(Fight).filter(Fight.is_deleted.is_(False)).all()

def insert_fight_stats_round(db: Session, fight_stats_round_data: dict) -> FightStatsRound:
    fight_stats_round = FightStatsRound(**fight_stats_round_data)
    db.add(fight_stats_round)
    return fight_stats_round

def delete_fight_stats_round(db: Session, fight_stats_round_id) -> bool:
    fight_stats_round = db.get(fight_stats_round_id)
    if not fight_stats_round:
        return False
    db.delete(fight_stats_round)
