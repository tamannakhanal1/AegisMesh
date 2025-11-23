# minimal risk scoring stub: assign higher risk if path /admin or service ssh, or payload contains 'password'
def score_event(e):
    score = 0.0
    if e.get("service") == "ssh":
        score += 0.5
    if e.get("path") and "/admin" in e.get("path"):
        score += 0.7
    p = (e.get("payload") or "").lower()
    if "password" in p or "login" in p:
        score += 0.6
    # clamp
    return min(score, 1.0)

# This file is a placeholder for future sklearn / clustering models
