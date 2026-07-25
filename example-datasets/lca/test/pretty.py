import json

with open("a3e150d0-770e-4e2a-9b19-f7daa8cda38b.json") as f:
    data = json.load(f)


with open("formatted.json", "w") as f:
    json.dump(data, f, indent=4)