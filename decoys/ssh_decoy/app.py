import socket, os, requests, threading
CONTROLLER_URL = os.getenv("CONTROLLER_URL", "http://localhost:8000/events")
HOST = "0.0.0.0"
PORT = 2222

BANNER_VARIANTS = [
    "SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7",
    "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3",
    "SSH-2.0-SSHD_5.3"
]

def handle_client(conn, addr):
    try:
        banner = BANNER_VARIANTS[hash(addr[0]) % len(BANNER_VARIANTS)]
        conn.send((banner + "\r\n").encode())
        # read one line then close
        data = conn.recv(1024).decode(errors="ignore")
        payload = data.strip()
        event = {
            "source_ip": addr[0],
            "service": "ssh",
            "path": None,
            "payload": payload or "banner_probe"
        }
        try:
            requests.post(CONTROLLER_URL, json=event, timeout=2)
        except:
            pass
        # send fake auth prompt, then close
        try:
            conn.send(b"Password: ")
            _ = conn.recv(1024)
        except:
            pass
    finally:
        conn.close()

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"SSH decoy listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    server()
