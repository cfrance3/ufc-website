from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class FighterBase(BaseModel):
    url: str
    name: str
    nickname: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    reach: Optional[str] = None
    stance: Optional[str] = None
    dob: Optional[str] = None
    record: Optional[str] = None

class FighterLite(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class Fighter(FighterBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class EventBase(BaseModel):
    name: str
    date: Optional[str] = None
    location: Optional[str] = None

class EventLite(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class Event(EventBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class FightBase(BaseModel):
    fighter1_outcome: str
    fighter2_outcome: str
    weightclass: str
    method: str
    round: str
    time: str
    title_fight: bool

class FightLite(BaseModel):
    id:int
    fighter1: FighterLite
    fighter2: FighterLite
    event: EventLite
    fighter1_outcome: str
    fighter2_outcome: str
    weightclass: Optional[str] = None
    method: Optional[str] = None
    round: Optional[str] = None
    time: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class Fight(FightBase):
    id: int
    fighter1: Fighter
    fighter2: Fighter
    event: Event
    
    model_config = ConfigDict(from_attributes=True)

class FightStatsRound(BaseModel):
    id: int
    round_number: int
    sig_strikes: Optional[int] = None
    sig_strike_percent: Optional[int] = None
    total_strikes: Optional[int] = None
    takedowns: Optional[int] = None
    takedown_percent: Optional[int] = None
    submissions_attempted: Optional[int] = None
    reversals: Optional[int] = None
    control_time_seconds: Optional[int] = None
    strikes_head: Optional[int] = None
    strikes_body: Optional[int] = None
    strikes_leg: Optional[int] = None
    strikes_distance: Optional[int] = None
    strikes_clinch: Optional[int] = None
    strikes_ground: Optional[int] = None
    knockdowns: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class FightStatsBase(BaseModel):
    fighter_id: int
    fight_id: int

class FightStats(FightStatsBase):
    id: int
    fighter: FighterLite
    fight: FightLite
    rounds: List[FightStatsRound] = []

    model_config = ConfigDict(from_attributes=True)

class FightStatsLite(FightStatsBase):
    id: int
    rounds: int
    fighter: FighterLite

    model_config = ConfigDict(from_attributes=True)