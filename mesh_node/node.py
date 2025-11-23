"""
AegisMesh mesh node agent
- Simulates normal and suspicious events
- Posts events to analyzer (http://analyzer:9000/events when running with docker-compose)
Run locally:
    python3 mesh_node/node.py --analyzer http://localhost:9000/events --mode simulate
"""
import requests, time, os, argparse, random, socket, json, datetime

DEFAULT_ANALYZER = os.environ.get("ANALYZER_URL", "http://analyzer:9000/events")

SAMPLE_NORMAL = [
    {"service": "http", "path": "/", "payload": "GET /"},
    {"service": "http", "path": "/about", "payload": "info_request"},
    {"service": "http", "path": "/api/status", "payload": "ping"},
]

SAMPLE_SUSPICIOUS = [
    {"service": "http", "path": "/admin", "payload": "admin_login_attempt"},
    {"service": "ssh", "path": None, "payload": "root"},
    {"service": "http", "path": "/wp-login.php", "payload": "wp-brute"},
    {"service": "ssh", "path": None, "payload": "Password: rootpwd"},
]

def send_event(url: str, e: dict):
    payload = {
        "source_ip": get_local_ip(),
        "service": e.get("service"),
        "path": e.get("path"),
        "payload": e.get("payload"),
        "ts": datetime.datetime.utcnow().isoformat() + "Z"
    }
    try:
        r = requests.post(url, json=payload, timeout=3)
        return True, r.status_code
    except Exception as ex:
        return False, str(ex)

def get_local_ip():
    # best-effort local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def simulate(analyzer_url, interval=3, suspicious_chance=0.15):
    print("Starting mesh node simulator ->", analyzer_url)
    while True:
        if random.random() < suspicious_chance:
            e = random.choice(SAMPLE_SUSPICIOUS)
        else:
            e = random.choice(SAMPLE_NORMAL)
        ok, code = send_event(analyzer_url, e)
        print(f"[{datetime.datetime.utcnow().isoformat()}] Sent {e['service']} {e.get('path')} -> ok={ok} code={code}")
        time.sleep(interval)

def one_shot(analyzer_url, event):
    ok, code = send_event(analyzer_url, event)
    print("one_shot", ok, code)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyzer", default=DEFAULT_ANALYZER, help="Analyzer URL /events endpoint")
    parser.add_argument("--mode", choices=["simulate", "oneshot"], default="simulate")
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--suspicious_chance", type=float, default=0.15)
    parser.add_argument("--event", type=str, help="JSON event for oneshot")
    args = parser.parse_args()

    if args.mode == "simulate":
        simulate(args.analyzer, interval=args.interval, suspicious_chance=args.suspicious_chance)
    else:
        if args.event:
            ev = json.loads(args.event)
            one_shot(args.analyzer, ev)
        else:
            print("Provide --event for oneshot mode")
