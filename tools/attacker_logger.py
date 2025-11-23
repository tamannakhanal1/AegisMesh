# Small helper to query the controller events and print summaries
import requests, os
URL = os.getenv("CONTROLLER_URL", "http://localhost:8000/events")
def fetch():
    r = requests.get(URL, timeout=5)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    events = fetch()
    print(f"Last {len(events)} events:")
    for e in events[:10]:
        print(e["timestamp"], e["source_ip"], e["service"], e["path"], "score:", e.get("risk_score"))
