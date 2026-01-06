from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Fighter(Base):
    __tablename__ = "fighters"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, index=True)
    nickname = Column(String, nullable=True)
    height = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    reach = Column(String, nullable=True)
    stance = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    record = Column(String, nullable=True)

    fights1 = relationship("Fight", back_populates="fighter1", foreign_keys='Fight.fighter1_id')
    fights2 = relationship("Fight", back_populates="fighter2", foreign_keys='Fight.fighter2_id')

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    date = Column(String, nullable=True)
    location = Column(String, nullable=True)

    fights = relationship("Fight", back_populates="event")

class Fight(Base):
    __tablename__ = "fights"

    id = Column(Integer, primary_key=True, index=True)
    fighter1_id = Column(Integer, ForeignKey("fighters.id"), index=True)
    fighter2_id = Column(Integer, ForeignKey("fighters.id"), index=True)
    fighter1_outcome = Column(String)
    fighter2_outcome = Column(String)
    weightclass = Column(String)
    method = Column(String)
    round = Column(String)
    time = Column(String)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)

    fighter1 = relationship("Fighter", foreign_keys=[fighter1_id], back_populates="fights1")
    fighter2 = relationship("Fighter", foreign_keys=[fighter2_id], back_populates="fights2")
    event = relationship("Event", back_populates="fights")