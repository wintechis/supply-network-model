import json

with open("0d95cc8b-a9a0-3630-a760-1ab4d88257d8.json") as f:
    data = json.load(f)


with open("formatted.json", "w") as f:
    json.dump(data, f, indent=4)