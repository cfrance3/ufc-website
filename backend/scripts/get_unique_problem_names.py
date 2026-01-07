import re
import unicodedata

def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.replace("\u00a0", " ")
    name = re.sub(r"\s+", " ", name)
    return name.strip().lower()


def extract_unique_names(log_text: str) -> list[str]:
    pattern = re.compile(r"Error with name (.+?) for bout")
    names = set()

    for line in log_text.splitlines():
        match = pattern.search(line)
        if match:
            raw_name = match.group(1)
            names.add(normalize_name(raw_name))

    return sorted(names)


if __name__ == "__main__":
    with open("backend/logs/warnings.log", "r", encoding="utf-8") as f:
        log_text = f.read()

    unique_names = extract_unique_names(log_text)

    with open("backend/logs/problem_fighters.log", "w", encoding="utf-8") as f:
        f.write(f"Total unique problematic fighters: {len(unique_names)}\n")
        for name in unique_names:
            f.write(f"{name}\n")
