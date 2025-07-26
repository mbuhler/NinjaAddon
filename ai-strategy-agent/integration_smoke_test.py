import requests
import json

with open("sample_payload.json", "r") as f:
    payload = json.load(f)

# The endpoint is /analyze/strategy, not /journal/entry
# Post entry
r = requests.post("http://localhost:8000/analyze/strategy", json=payload)
print("Entry POST:", r.status_code)

# Summary
r = requests.get("http://localhost:8000/journal/summary/AllWeather_NQ_v38")
print("Summary:", r.json())

# Theme summary
r = requests.get("http://localhost:8000/journal/themes/AllWeather_NQ_v38")
print("Themes:", r.json())

# Export
r = requests.get("http://localhost:8000/export/training-set")
with open("training_set.jsonl", "wb") as f:
    f.write(r.content)
print("Exported training set.")
