import json
from pathlib import Path

input_dir = Path("USLCI_Database/processes")
output_dir = Path("USLCI_Database/formatted")

# Create output directory if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)

for input_file in input_dir.glob("*.json"):
    output_file = output_dir / input_file.name

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)