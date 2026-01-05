import sqlite3
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "ufc.db"
FIGHTERS_CSV = BASE_DIR / "data" / "fighters.csv"
FIGHTS_CSV = BASE_DIR / "data" / "fights.csv"
NICKNAMES_CSV = BASE_DIR / "data" / "nicknames.csv"

# Helper functions

def parse_fight_outcome(outcome_str):
    outcome_str = outcome_str.strip().upper()
    if outcome_str == "W/L":
        return ("win", "loss")
    elif outcome_str == "L/W":
        return ("loss", "win")
    elif outcome_str == "D/D":
        return ("draw", "draw")
    elif outcome_str == "NC/NC":
        return ("nc", "nc")
    else:
        # fallback for unknown results
        return ("unknown", "unknown")
    
def clean_csv_value(value: str):
    """Remove extra quotes, trim whitespace, return None if empty"""
    if not value:
        return None
    return value.replace('""', '"').strip()

def main():
    # Connect
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Create tables 
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fighters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        nickname TEXT,
        height TEXT,
        weight TEXT,
        reach TEXT,
        stance TEXT,
        dob TEXT,
        record TEXT
            )
        """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fighter1 TEXT,
        fighter2 TEXT,
        fighter1_outcome TEXT,
        fighter2_outcome TEXT,
        weightclass TEXT,
        method TEXT,
        round TEXT,
        time TEXT,
        event
    )
    """)

    # Import fighters
    with open(FIGHTERS_CSV, newline="", encoding="utf-8") as fr:
        reader = csv.DictReader(fr)

        for row in reader:
            cur.execute("""
                INSERT OR IGNORE INTO fighters(
                    name, height, weight, reach, stance, dob)
                 VALUES (?, ?, ?, ?, ?, ?)
            """, (
                clean_csv_value(row.get("FIGHTER")),
                clean_csv_value(row.get("HEIGHT")),
                clean_csv_value(row.get("WEIGHT")),
                clean_csv_value(row.get("REACH")),
                clean_csv_value(row.get("STANCE")),
                clean_csv_value(row.get("DOB"))
            ))

    # Update nicknames
    with open(NICKNAMES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            first = clean_csv_value(row.get("FIRST"))
            last = clean_csv_value(row.get("Last"))
            nickname = clean_csv_value(row.get("NICKNAME"))
            full_name = f"{first} {last}"

            if nickname:
                cur.execute("""
                UPDATE fighters SET nickname = ?
                WHERE name = ?
                """, (nickname, full_name))

    # Import fights
    with open(FIGHTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bout = row.get("BOUT")
            if not bout or "vs." not in bout:
                continue
            fighter1, fighter2 = [clean_csv_value(fr.strip()) for fr in bout.split("vs.")]
            f1_outcome, f2_outcome = parse_fight_outcome(row.get("OUTCOME"))

            cur.execute("""
            INSERT INTO fights
            (fighter1, fighter2, fighter1_outcome, fighter2_outcome, weightclass, method, round, time, event)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fighter1,
                fighter2,
                f1_outcome,
                f2_outcome,
                clean_csv_value(row.get("WEIGHTCLASS")),
                clean_csv_value(row.get("METHOD")),
                clean_csv_value(row.get("ROUND")),
                clean_csv_value(row.get("TIME")),
                clean_csv_value(row.get("EVENT"))
            ))

    conn.commit()

    # Compute fighter records
    cur.execute("SELECT name FROM fighters")
    fighter_names = [row["name"] for row in cur.fetchall()]

    for fname in fighter_names:
        cur.execute("""
        SELECT fighter1_outcome AS outcome FROM fights WHERE fighter1 = ?
        UNION ALL
        SELECT fighter2_outcome AS outcome FROM fights WHERE fighter2 = ?
        """, (fname, fname))
        outcomes = [r[0] for r in cur.fetchall()]
        wins = outcomes.count("win")
        losses = outcomes.count("loss")
        draws = outcomes.count("draw")
        record = f"{wins}-{losses}-{draws}"
        cur.execute("UPDATE fighters SET record = ? WHERE name = ?", (record, fname))

    conn.commit()
    conn.close()
    print("Imported fighters, nicknames, fights, and updated records successfully.")

if __name__ == "__main__":
    main()