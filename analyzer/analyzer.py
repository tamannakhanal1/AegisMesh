"""
AegisMesh Analyzer Service
- FastAPI app that accepts events at /events
- Stores events in a simple JSON-lines log (logs/events.log)
- Produces a risk_score using either sklearn IsolationForest (if available)
  or a compact rule-based fallback.
Run: uvicorn analyzer:app --host 0.0.0.0 --port 9000
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os, json, datetime, threading, time

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "events.log")

# Try to import sklearn for a better anomaly detector
USE_SK = False
try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    USE_SK = True
except Exception:
    USE_SK = False

app = FastAPI(title="AegisMesh Analyzer", version="0.1")

class EventIn(BaseModel):
    source_ip: str
    service: str
    path: Optional[str] = None
    payload: Optional[str] = None
    ts: Optional[str] = None

# Simple in-memory buffer for recent events used by the ML model
BUFFER = []
BUFFER_LOCK = threading.Lock()
MAX_BUFFER = 1000

# If sklearn available, maintain a trained model in background
MODEL = None
MODEL_LOCK = threading.Lock()

def append_log(evt: dict):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(evt) + "\n")

def rule_score(evt: dict) -> float:
    """Fallback deterministic scoring (0.0 - 1.0)."""
    score = 0.0
    service = (evt.get("service") or "").lower()
    path = (evt.get("path") or "").lower()
    payload = (evt.get("payload") or "").lower()

    if service in ("ssh", "rlogin", "telnet"):
        score += 0.4
    if "/admin" in path or "login" in payload or "password" in payload:
        score += 0.5
    if "curl" in payload or "wget" in payload or "scan" in payload:
        score += 0.3
    # Suspicious short or binary-like payloads
    if payload and (len(payload) < 6 or any(c in payload for c in "<>{}[]$;\\|")):
        score += 0.2
    return min(score, 1.0)

def vectorize(evt: dict):
    """
    Convert event to numeric vector for simple ML:
    [service_ssh, has_admin_path, payload_len, weird_chars_count]
    """
    service = (evt.get("service") or "").lower()
    payload = (evt.get("payload") or "") or ""
    path = (evt.get("path") or "") or ""
    service_ssh = 1 if service in ("ssh",) else 0
    has_admin = 1 if "/admin" in path.lower() else 0
    payload_len = len(payload)
    weird = sum(1 for c in payload if c in "<>{}[]$;\\|")
    return [service_ssh, has_admin, payload_len, weird]

def train_model_if_needed():
    global MODEL
    if not USE_SK:
        return
    with MODEL_LOCK:
        try:
            import numpy as np
            from sklearn.ensemble import IsolationForest
            with BUFFER_LOCK:
                if len(BUFFER) < 50:
                    return
                X = np.array([vectorize(e) for e in BUFFER])
            # Keep contamination low to flag only a few points
            model = IsolationForest(contamination=0.02, random_state=42)
            model.fit(X)
            MODEL = model
        except Exception as e:
            print("Model training error:", e)
            MODEL = None

def periodic_retrain():
    while True:
        train_model_if_needed()
        time.sleep(30)

# Start background retrain thread if sklearn is available
if USE_SK:
    t = threading.Thread(target=periodic_retrain, daemon=True)
    t.start()

@app.post("/events")
def receive_event(event: EventIn):
    evt = event.dict()
    evt["ts"] = evt.get("ts") or datetime.datetime.utcnow().isoformat() + "Z"
    # Append to file
    append_log(evt)
    # Add to buffer
    with BUFFER_LOCK:
        BUFFER.append(evt)
        if len(BUFFER) > MAX_BUFFER:
            BUFFER.pop(0)

    # Score
    score = 0.0
    if USE_SK and MODEL is not None:
        try:
            import numpy as np
            v = np.array(vectorize(evt)).reshape(1, -1)
            # IsolationForest: negative_outlier_factor => we use decision_function
            val = MODEL.decision_function(v)[0]  # higher -> normal, lower -> anomaly
            # Map decision_function output to 0..1 risk (approx)
            # decision_function range is model dependent; do a soft mapping
            score = float(max(0.0, min(1.0, (0.5 - val) + 0.5)))
        except Exception:
            score = rule_score(evt)
    else:
        score = rule_score(evt)

    evt["risk_score"] = round(float(score), 3)
    # Update log with score (append a separate scored line)
    append_log({"scored_event": evt})
    return {"status": "ok", "risk_score": evt["risk_score"]}

@app.get("/health")
def health():
    return {"status": "ok", "use_sklearn": USE_SK, "buffer_size": len(BUFFER)}

@app.get("/events")
def fetch_events(limit: int = 200):
    out = []
    try:
        if not os.path.exists(LOG_FILE):
            return out
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    j = json.loads(line.strip())
                    out.append(j)
                except:
                    continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return list(reversed(out))[:limit]
