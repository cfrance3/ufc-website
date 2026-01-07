from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
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

    fight_stats = relationship("FightStats", back_populates="fighter", cascade="all, delete-orphan")

    fights_as_fighter1 = relationship("Fight", back_populates="fighter1", foreign_keys='Fight.fighter1_id')
    fights_as_fighter2 = relationship("Fight", back_populates="fighter2", foreign_keys='Fight.fighter2_id')

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
    fighter1_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), index=True)
    fighter2_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), index=True)
    fighter1_outcome = Column(String)
    fighter2_outcome = Column(String)
    weightclass = Column(String)
    method = Column(String)
    round = Column(String)
    time = Column(String)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), index=True)

    fighter1 = relationship("Fighter", foreign_keys=[fighter1_id], back_populates="fights_as_fighter1")
    fighter2 = relationship("Fighter", foreign_keys=[fighter2_id], back_populates="fights_as_fighter2")
    fight_stats = relationship("FightStats", back_populates="fight", cascade="all, delete-orphan")
    event = relationship("Event", back_populates="fights")

class FightStats(Base):
    __tablename__ = "fight_stats"

    id = Column(Integer, primary_key=True, index=True)
    fight_id = Column(Integer, ForeignKey("fights.id", ondelete="CASCADE"), nullable=False)
    fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False)

    fighter = relationship("Fighter", back_populates="fight_stats")
    fight = relationship("Fight", back_populates="fight_stats")
    rounds = relationship("FightStatsRound", back_populates="fight_stats", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('fight_id', 'fighter_id', name='_fight_fighter_uc'),
    )

class FightStatsRound(Base):
    __tablename__ = "fight_stats_round"

    id = Column(Integer, primary_key=True, index=True)
    fight_stats_id = Column(Integer, ForeignKey("fight_stats.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)

    sig_strikes = Column(Integer, nullable=True)
    sig_strike_percent = Column(Integer, nullable=True)
    total_strikes = Column(Integer, nullable=True)
    takedowns = Column(Integer, nullable=True)
    takedown_percent = Column(Integer, nullable=True)
    submissions_attempted = Column(Integer, nullable=True)
    reversals = Column(Integer, nullable=True)
    control_time_seconds = Column(Integer, nullable=True)
    strikes_head = Column(Integer, nullable=True)
    strikes_body = Column(Integer, nullable=True)
    strikes_leg = Column(Integer, nullable=True)
    strikes_distance = Column(Integer, nullable=True)
    strikes_clinch = Column(Integer, nullable=True)
    strikes_ground = Column(Integer, nullable=True)
    knockdowns = Column(Integer, nullable=True)

    fight_stats = relationship("FightStats", back_populates="rounds")

    __table_args__ = (
        UniqueConstraint('fight_stats_id', 'round_number', name='_fightstats_round_uc'),
    )

