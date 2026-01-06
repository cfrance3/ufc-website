from pydantic import BaseModel
from typing import Optional

class FighterBase(BaseModel):
    name: str
    nickname: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    reach: Optional[str] = None
    stance: Optional[str] = None
    dob: Optional[str] = None
    record: Optional[str] = None

class Fighter(FighterBase):
    id: int
    class Config:
        orm_mode = True

class EventBase(BaseModel):
    name: str
    date: Optional[str] = None
    location: Optional[str] = None

class Event(EventBase):
    id: int
    class Config:
        orm_mode = True

class FightBase(BaseModel):
    fighter1_outcome: str
    fighter2_outcome: str
    weightclass: str
    method: str
    round: str
    time: str

class Fight(FightBase):
    id: int
    fighter1: Fighter
    fighter2: Fighter
    event: Event
    class Config:
        orm_mode = True