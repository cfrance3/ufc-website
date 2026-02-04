import csv
import json
import re
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from collections import defaultdict
import unicodedata
from backend.app.scraper import scrape_fighters_from_fight
from backend.app.crud.fighters import upsert_fighter, update_fighter, get_fighter_by_url
from backend.app.crud.events import upsert_event, get_event_by_name
from backend.app.crud.fights import insert_fight, get_fight_by_event_and_fighters, get_fight_by_bout_and_event_name
from backend.app.crud.fight_stats import get_or_create_fight_stats
from backend.app.crud.fight_stats_rounds import insert_fight_stats_round
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
    
def parse_record(record: str) -> tuple[int, int, int, int]:
    parts = record.split(",")

    wld = parts[0].strip().split('-')
    wins = int(wld[0])
    losses = int(wld[1])
    draws = int(wld[2])

    nc_part = parts[1].strip()
    nc = int(nc_part[:-2].strip())

    return wins, losses, draws, nc

def parse_bout(bout: str) -> tuple[str, str]:
    names = bout.split("vs.")
    f1_name = normalize_name(names[0])
    f2_name = normalize_name(names[1])
    return f1_name, f2_name

    
def resolve_fighter_url(
        fighter_name: str,
        fight_url: str | None,
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
        else:
            logging.warning(f"Duplicate name mismatch: '{fighter_name}' on {fight_url}")
            logging.info(f"URL tried: {scraped_url}, URLs found: {urls}")
            return None
    
    # Name not found
    logging.warning(f"Unknown fighter name '{fighter_name}' on {fight_url}")
    return None

def parse_x_of_y(stat: str) -> tuple[int, int]:
    if "of" not in stat:
        return 0,0
    x,y = stat.split("of")
    
    return to_int(x.strip()), to_int(y.strip())

def parse_time_into_seconds(time: str) -> int:
    if ":" not in time:
        return 0
    split = time.split(":")
    m = int(split[0])
    s = int(split[1])
    return (m*60) + s

def to_int(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    value = str(value).strip()

    if value in {"", "---", "NULL", "None"}:
        return None

    try:
        return int(value)
    except ValueError:
        try:
            return int(float(value))  # handles "0.0", "1.0"
        except ValueError:
            return None
    
def parse_round_value(value: str):
    return re.sub(r"Round\s*", "", value)
    
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
                "event_id": event.id,
                "url": fight_url
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

    with open(stats_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bout = clean_csv_value(row.get("BOUT"))
            event_name = clean_csv_value(row.get("EVENT"))
            event = get_event_by_name(db, event_name)
            fight = get_fight_by_bout_and_event_name(db, bout, event_name)
            fight_url = fight.url


            f1_name, f2_name = parse_bout(bout)
            f1 = fight.fighter1
            f2 = fight.fighter2
            fighter_name = normalize_name(row.get("FIGHTER"))
            
            if fighter_name is None:
                logging.info(f"Fighter name is None. Inserting blank rows")
                fight_stats1 = get_or_create_fight_stats(db, fight.id, f1.id)
                fight_stats1_round_data = {
                "fight_stats_id": fight_stats1.id,
                "round_number": None,
                "sig_strikes": None,
                "sig_strikes_attempted": None,
                "total_strikes": None,
                "total_strikes_attempted": None,
                "takedowns": None,
                "takedowns_attempted": None,
                "submissions_attempted": None,
                "reversals": None,
                "control_time_seconds": None,
                "strikes_head": None,
                "strikes_head_attempted": None,
                "strikes_body": None,
                "strikes_body_attempted": None,
                "strikes_leg": None,
                "strikes_leg_attempted": None,
                "strikes_distance": None,
                "strikes_clinch": None,
                "strikes_ground": None,
                "knockdowns": None,
                "fight_stats": fight_stats1
                }

                fight_stats2 = get_or_create_fight_stats(db, fight.id, f2.id)
                fight_stats2_round_data = {
                "fight_stats_id": fight_stats2.id,
                "round_number": None,
                "sig_strikes": None,
                "sig_strikes_attempted": None,
                "total_strikes": None,
                "total_strikes_attempted": None,
                "takedowns": None,
                "takedowns_attempted": None,
                "submissions_attempted": None,
                "reversals": None,
                "control_time_seconds": None,
                "strikes_head": None,
                "strikes_head_attempted": None,
                "strikes_body": None,
                "strikes_body_attempted": None,
                "strikes_leg": None,
                "strikes_leg_attempted": None,
                "strikes_distance": None,
                "strikes_clinch": None,
                "strikes_ground": None,
                "knockdowns": None,
                "fight_stats": fight_stats2
                }

                insert_fight_stats_round(db, fight_stats1_round_data)
                insert_fight_stats_round(db, fight_stats2_round_data)
                
            else:
                if fighter_name == f1_name:
                    fighter = f1
                elif fighter_name == f2_name:
                    fighter = f2
                else:
                    logging.warning(f"Fighter {fighter_name} did not match either fighter: {f1_name}, {f2_name}")
                    continue

                fight_stats = get_or_create_fight_stats(db, fight.id, fighter.id)

                round_num = to_int(parse_round_value(row.get("ROUND")))
                sig_strikes, sig_strikes_att = parse_x_of_y(clean_csv_value(row.get("SIG.STR.")))
                tot_strikes, tot_strikes_att = parse_x_of_y(clean_csv_value(row.get("TOTAL STR.")))
                takedowns, takedowns_att = parse_x_of_y(clean_csv_value(row.get("TD")))
                submissions_att = to_int(clean_csv_value(row.get("SUB.ATT")))
                reversals = to_int(clean_csv_value(row.get("REV.")))
                control_time_seconds = parse_time_into_seconds(clean_csv_value(row.get("CTRL")))
                head, head_att = parse_x_of_y(clean_csv_value(row.get("HEAD")))
                body, body_att = parse_x_of_y(clean_csv_value(row.get("BODY")))
                leg, leg_att = parse_x_of_y(clean_csv_value(row.get("LEG")))
                distance = parse_x_of_y(clean_csv_value(row.get("DISTANCE")))[0]
                clinch = parse_x_of_y(clean_csv_value(row.get("CLINCH")))[0]
                ground = parse_x_of_y(clean_csv_value(row.get("GROUND")))[0]
                knockdowns = to_int(clean_csv_value(row.get("KD")))

                fight_stats_round_data = {
                    "fight_stats_id": fight_stats.id,
                    "round_number": round_num,
                    "sig_strikes": sig_strikes,
                    "sig_strikes_attempted": sig_strikes_att,
                    "total_strikes": tot_strikes,
                    "total_strikes_attempted": tot_strikes_att,
                    "takedowns": takedowns,
                    "takedowns_attempted": takedowns_att,
                    "submissions_attempted": submissions_att,
                    "reversals": reversals,
                    "control_time_seconds": control_time_seconds,
                    "strikes_head": head,
                    "strikes_head_attempted": head_att,
                    "strikes_body": body,
                    "strikes_body_attempted": body_att,
                    "strikes_leg": leg,
                    "strikes_leg_attempted": leg_att,
                    "strikes_distance": distance,
                    "strikes_clinch": clinch,
                    "strikes_ground": ground,
                    "knockdowns": knockdowns,
                    "fight_stats": fight_stats
                }

                insert_fight_stats_round(db, fight_stats_round_data)  
        

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
