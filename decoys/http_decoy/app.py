from flask import Flask, request, jsonify
import os, requests
app = Flask(__name__)
CONTROLLER_URL = os.getenv("CONTROLLER_URL", "http://localhost:8000/events")

@app.route("/", methods=["GET", "POST", "PUT", "DELETE"])
def homepage():
    data = {
        "source_ip": request.remote_addr,
        "service": "http",
        "path": request.path,
        "payload": str(request.get_data(as_text=True) or request.args)
    }
    try:
        requests.post(CONTROLLER_URL, json=data, timeout=2)
    except Exception:
        pass
    # Fake realistic app response / banner variation
    return "Welcome to Acme WebApp v2.1.4\n", 200

@app.route("/admin", methods=["GET"])
def admin():
    data = {
        "source_ip": request.remote_addr,
        "service": "http",
        "path": "/admin",
        "payload": "access_attempt"
    }
    try:
        requests.post(CONTROLLER_URL, json=data, timeout=2)
    except Exception:
        pass
    return "Admin login\n", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
