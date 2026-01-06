import csv
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from backend.app import models
from backend.app.crud.fighters import upsert_fighter


# Create tables
Base.metadata.create_all(bind=engine)

def clean_csv_value(value: str):
    if not value:
        return None
    return value.replace('""', '"').strip()

def parse_fight_outcome(outcome: str):
    outcome = outcome.upper().strip()
    if outcome == "W/L":
        return "win", "loss"
    elif outcome == "L/W":
        return "loss", "win"
    elif outcome == "D/D":
        return "draw", "draw"
    else:
        return "unknown", "unknown"
    
def import_data(fighters_file, nicknames_file, events_file, fights_file):
    db: Session = SessionLocal()

    # Import fighters
    fighters_dict = {}
    with open(fighters_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
           fighter_data = {
               "name": clean_csv_value(row.get("FIGHTER")),
               "nickname": None,
               "height": clean_csv_value(row.get("HEIGHT")),
               "weight": clean_csv_value(row.get("WEIGHT")),
               "reach": clean_csv_value(row.get("REACH")),
                "stance": clean_csv_value(row.get("STANCE")),
                "dob": clean_csv_value(row.get("DOB")),
                "record": None
           }
           fighter = upsert_fighter(db, fighter_data)
           fighters_dict[fighter.name] = fighter

    # Update nicknames
    with open(nicknames_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_name = clean_csv_value(f"{row.get('FIRST')} {row.get('LAST')}")
            nickname = clean_csv_value(row.get("NICKNAME"))
            if full_name in fighters_dict and nickname:
                fighter = fighters_dict[full_name]
                fighter.nickname = nickname
                db.add(fighter)
        db.commit()

    # Import events
    events_dict = {}
    with open(events_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = clean_csv_value(row.get("EVENT"))
            event = models.Event(
                name = name,
                date=clean_csv_value(row.get("DATE")),
                location=clean_csv_value(row.get("LOCATION"))
            )
            db.add(event)
            events_dict[name] = event
    db.commit()

    # Import fights
    with open(fights_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bout = clean_csv_value(row.get("BOUT"))
            if "vs." not in bout:
                continue
            fighter1_name, fighter2_name = [fr.strip() for fr in bout.split("vs.")]
            fighter1 = fighters_dict.get(fighter1_name)
            fighter2 = fighters_dict.get(fighter2_name)
            if not fighter1 or not fighter2:
                continue
            f1_outcome, f2_outcome = parse_fight_outcome(clean_csv_value(row.get("OUTCOME")))
            event = events_dict.get(clean_csv_value(row.get("EVENT")))
            if not event:
                continue

            fight = models.Fight(
                fighter1_id=fighter1.id,
                fighter2_id=fighter2.id,
                fighter1_outcome=f1_outcome,
                fighter2_outcome=f2_outcome,
                weightclass=clean_csv_value(row.get("WEIGHTCLASS")),
                method=clean_csv_value(row.get("METHOD")),
                round=clean_csv_value(row.get("ROUND")),
                time=clean_csv_value(row.get("TIME")),
                event_id=event.id
            )
            db.add(fight)

    db.commit()
    db.close()

    
if __name__ == "__main__":
    import_data(
        fighters_file="backend/data/fighters.csv",
        nicknames_file="backend/data/nicknames.csv",
        events_file="backend/data/events.csv",
        fights_file="backend/data/fights.csv"
    )
