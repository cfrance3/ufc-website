from pydantic import BaseModel, ConfigDict
from typing import Optional

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