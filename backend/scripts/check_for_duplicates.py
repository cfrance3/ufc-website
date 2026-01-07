import csv
from collections import Counter

with open("backend/data/fighters.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    names = [row["FIGHTER"].strip() for row in reader if row["FIGHTER"].strip()]
    counts = Counter(names)

duplicates = {name: count for name, count in counts.items() if count > 1}
print("Duplicate names in CSV:", duplicates)
print("Total unique fighters in CSV:", len(set(names)))
