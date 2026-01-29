import csv
import json
import re
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from collections import defaultdict
import unicodedata
from backend.app.scraper import scrape_fighters_from_fight
from backend.app.crud.fighters import upsert_fighter, update_fighter
from backend.app.crud.events import upsert_event
from backend.app.crud.fights import insert_fight
from backend.app.models import TitleStatus
from backend.app.constants import WEIGHTCLASS_TO_WEIGHT

import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("backend/logs/import.log", encoding="utf-8"),
        # logging.StreamHandler()
    ]
)

# Create tables
Base.metadata.create_all(bind=engine)

def clean_csv_value(value: str):
    if not value:
        return None
    return value.replace('""', '"').strip()

def normalize_name(name: str) -> str:
    if not name:
        return None
    # normalize unicode characters
    name = unicodedata.normalize('NFKD', name)
    # replace non-breaking spaces
    name = name.replace('\xa0', ' ')
    # collapse multiple spaces into one and lowercase
    name = ' '.join(name.strip().split())
    return name

def normalize_weightclass(raw: str) -> str:
    """
    Convert raw weightclass string from fight table to standard weightclass.
    Examples:
        "Featherweight Bout" -> "Featherweight"
        "UFC Light Heavyweight Title Bout" -> "Light Heavyweight"
    """
    if not raw:
        return "Unknown"

    # Remove 'UFC', 'Title', 'Bout', etc.
    cleaned = re.sub(r'\b(UFC|Title|Bout)\b', '', raw, flags=re.IGNORECASE)

    # Remove extra spaces
    cleaned = ' '.join(cleaned.split()).strip()

    for wc in WEIGHTCLASS_TO_WEIGHT.keys():
        if re.search(rf'\b{wc}\b', cleaned, flags=re.IGNORECASE):
            return wc
        
    return "Open Weight"


    return cleaned

def get_title_status(bout_type: str):
    if re.search(r"\binterim\b", bout_type, re.IGNORECASE) is not None:
        return TitleStatus.INTERIM
    elif bool(re.search(r"\btitle\b", bout_type, re.IGNORECASE)):
        return TitleStatus.UNDISPUTED
    else:
        return TitleStatus.NONE
    
    

def parse_fight_outcome(outcome: str):
    outcome = outcome.upper().strip()
    if outcome == "W/L":
        return "W", "L"
    elif outcome == "L/W":
        return "L", "W"
    elif outcome == "D/D":
        return "D", "D"
    elif outcome == "NC/NC":
        return "NC", "NC"
    else:
        return "unknown", "unknown"
    
def parse_record(record: str):
    parts = record.split(",")

    wld = parts[0].strip().split('-')
    wins = int(wld[0])
    losses = int(wld[1])
    draws = int(wld[2])

    nc_part = parts[1].strip()
    nc = int(nc_part[:-2].strip())

    return wins, losses, draws, nc

    
def resolve_fighter_url(
        fighter_name: str,
        fight_url: str,
        name_to_urls: dict[str, list[str]],
        scraped_urls: dict | None,
        position: str,
        fighters_dict: dict[str, object]
) -> str | None:

    # Has scraped URL
    if scraped_urls:
        scraped_url = scraped_urls.get(position)
        if scraped_url in fighters_dict:
            return scraped_url
        
    urls = name_to_urls.get(fighter_name, [])
    # Unique name, no scraping
    if len(urls) == 1:
        return urls[0]
    
    # Duplicate name, scraped URL matches one
    if len(urls) > 1 and scraped_urls:
        scraped_url = scraped_urls.get(position)
        if scraped_url in urls:
            return scraped_url
        
        logging.warning(f"Duplicate name mismatch: '{fighter_name}' on {fight_url}")
        return None
    
    # Name not found
    logging.warning(f"Unknown fighter name '{fighter_name}' on {fight_url}")
    return None
    
def import_data(fighters_file, nicknames_file, events_file, fights_file, stats_file):
    db: Session = SessionLocal()

    # Import fighters
    fighters_dict = {} # key = fighter URL
    name_to_urls = defaultdict(list) # map from name to url of all fighters with that name
    scraped_name_to_urls = defaultdict(set) # map from name to scraped urls (for missing or bad data)

    with open(fighters_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fighter_data = {
               "url": clean_csv_value(row.get("URL")),
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
            fighters_dict[fighter.url] = fighter

            norm = normalize_name(fighter.name)
            if norm:
                name_to_urls[norm].append(fighter.url)
           
    db.flush()
               
    # Add known name -> url mappings from JSON
    scraped_map_path = Path("backend/data/scraped_fighter_name_map.json")
    if scraped_map_path.exists():
        with scraped_map_path.open("r", encoding="utf-8") as f:
            previous_scraped_map = json.load(f)

        for name, urls in previous_scraped_map.items():
            norm = normalize_name(name)
            for url in urls:
                if url not in name_to_urls[norm]:
                    name_to_urls[norm].append(url)

        logging.info(f"Loaded {len(previous_scraped_map)} previously scraped fighter names")

    # Update nicknames
    with open(nicknames_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fighter_url = clean_csv_value(row.get("URL"))
            nickname = clean_csv_value(row.get("NICKNAME"))
            
            if fighter_url in fighters_dict and nickname:
                fighter = fighters_dict[fighter_url]
                fighter_data = {"nickname": nickname}
                update_fighter(db, fighter.id, fighter_data)
    db.flush()

    # Import events
    events_dict = {} # key = event name
    with open(events_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = clean_csv_value(row.get("EVENT"))
            event_data = {
                "name": name,
                "date": clean_csv_value(row.get("DATE")),
                "location": clean_csv_value(row.get("LOCATION"))
            }
            event = upsert_event(db, event_data)
            events_dict[name] = event
    db.flush()

    # Load previously scraped fight URL map
    scraped_fight_map_path = Path("backend/data/scraped_fight_url_map.json")
    scraped_fight_url_map = {}

    if scraped_fight_map_path.exists() and scraped_fight_map_path.stat().st_size > 0:
        with scraped_fight_map_path.open("r", encoding="utf-8") as f:
            scraped_fight_url_map = json.load(f)

        logging.info(f"Loaded {len(scraped_fight_url_map)} previously scraped fight URLs")

    # Import fights and build records
    with open(fights_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bout = clean_csv_value(row.get("BOUT"))
            if "vs." not in bout:
                continue

            fighter1_name, fighter2_name = [normalize_name(fr) for fr in bout.split("vs.")]
            fight_url = clean_csv_value(row.get("URL"))

            if fight_url in scraped_fight_url_map:
                logging.info(f"Using previously scraped URLs for fight {fight_url}")
                f1_scraped = scraped_fight_url_map[fight_url]["fighter1"]
                f2_scraped = scraped_fight_url_map[fight_url]["fighter2"]
                scraped_urls = {
                    "fighter1": f1_scraped,
                    "fighter2": f2_scraped
                }
            else:

                # Decide if scraping is needed
                needs_scrape = (
                    len(name_to_urls.get(fighter1_name, [])) != 1 or
                    len(name_to_urls.get(fighter2_name, [])) != 1
                )

                scraped_urls = None
                if needs_scrape:
                    logging.info(
                        f"Scraping fight page for duplicate resolution: "
                        f"{fighter1_name} vs {fighter2_name}"
                    )
                    f1_scraped, f2_scraped = scrape_fighters_from_fight(fight_url)
                    scraped_urls = {
                        "fighter1": f1_scraped,
                        "fighter2": f2_scraped
                    }

                    scraped_fight_url_map[fight_url] = {
                        "fighter1": f1_scraped,
                        "fighter2": f2_scraped
                    }

            fighter1_url = resolve_fighter_url(
                fighter1_name,
                fight_url,
                name_to_urls,
                scraped_urls,
                "fighter1",
                fighters_dict
            )

            fighter2_url = resolve_fighter_url(
                fighter2_name,
                fight_url,
                name_to_urls,
                scraped_urls,
                "fighter2",
                fighters_dict
            )

            if scraped_urls:
                if fighter1_url:
                    scraped_name_to_urls[fighter1_name].add(fighter1_url)
                if fighter2_url:
                    scraped_name_to_urls[fighter2_name].add(fighter2_url)


            fighter1 = fighters_dict.get(fighter1_url)
            fighter2 = fighters_dict.get(fighter2_url)

            if not fighter1 or not fighter2:
                logging.warning(
                    f"Could not resolve fighers for bout '{bout}'"
                    f"f1={fighter1_url}, f2={fighter2_url}"
                )
                continue

            event = events_dict.get(clean_csv_value(row.get("EVENT")))
            if not event:
                logging.warning(f"No event found for bout '{bout}'")

            f1_outcome, f2_outcome = parse_fight_outcome(clean_csv_value(row.get("OUTCOME")))

            fight_data = {
                "bout_name": clean_csv_value(row.get("BOUT")),
                "fighter1_id": fighter1.id,
                "fighter2_id": fighter2.id,
                "fighter1_outcome": f1_outcome,
                "fighter2_outcome": f2_outcome,
                "weightclass": normalize_weightclass(clean_csv_value(row.get("WEIGHTCLASS"))),
                "method": clean_csv_value(row.get("METHOD")),
                "round": clean_csv_value(row.get("ROUND")),
                "time": clean_csv_value(row.get("TIME")),
                "title_status": get_title_status(row.get("WEIGHTCLASS")),
                "event_id": event.id
            }
            insert_fight(db, fight_data)

            # Update fighter records
            for fighter, outcome in [(fighter1, f1_outcome), (fighter2, f2_outcome)]:
                if not fighter.record:
                    wins = losses = draws = no_contests = 0
                else:
                    wins, losses, draws, no_contests = parse_record(fighter.record)

                if outcome == "W":
                    wins += 1
                elif outcome == "L":
                    losses += 1
                elif outcome == "D":
                    draws += 1
                elif outcome == "NC":
                    no_contests += 1

                record = f"{wins}-{losses}-{draws}, {no_contests}NC"
                fighter_data = {"record": record}
                update_fighter(db, fighter.id, fighter_data)
    db.flush()

    output_fighter_path = Path("backend/data/scraped_fighter_name_map.json")

    with output_fighter_path.open("w", encoding="utf-8") as f:
        json.dump(
            {name: sorted(urls) for name, urls in scraped_name_to_urls.items()},
            f,
            indent=2,
            ensure_ascii=False
        )
    logging.info(f"Wrote scraped fighter name map to {output_fighter_path}")

    output_fight_path = Path("backend/data/scraped_fight_url_map.json")
    with output_fight_path.open("w", encoding="utf-8") as f:
        json.dump(scraped_fight_url_map, f, indent=2, ensure_ascii=False)
    logging.info(f"Wrote scraped fight URL map to {output_fight_path}")


    db.commit()
    db.close()

    
if __name__ == "__main__":
    import_data(
        fighters_file="backend/data/fighters.csv",
        nicknames_file="backend/data/nicknames.csv",
        events_file="backend/data/events.csv",
        fights_file="backend/data/fights.csv",
        stats_file="backend/data/stats.csv"
    )
