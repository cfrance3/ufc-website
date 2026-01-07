from pathlib import Path

def extract_warnings(input_log: str, output_log: str):
    input_path = Path(input_log)
    output_path = Path(output_log)

    with input_path.open("r", encoding="utf-8") as infile, \
         output_path.open("w", encoding="utf-8") as outfile:

        for line in infile:
            if "[WARNING]" in line:
                outfile.write(line)

    print(f"Extracted warnings written to {output_path}")


if __name__ == "__main__":
    extract_warnings(
        input_log="backend/logs/import.log",
        output_log="backend/logs/warnings.log"
    )
