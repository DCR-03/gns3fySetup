# client_node.py
import socket
import requests
import threading
import uuid
import time
import random
import string
from datetime import datetime

CONTROL_HOST = "10.10.0.1"
CONTROL_PORT = 9000
SERVER_NODE = "10.10.0.2:8080"  # HTTP server target
client_id = str(uuid.uuid4())

running = False

def random_string(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def send_requests():
    global running
    while True:
        if running:
            payload = {
                "id": client_id,
                "ts": datetime.utcnow().isoformat(),
                "rand": random_string()
            }
            try:
                r = requests.get(f"http://{SERVER_NODE}/data?{payload}")
                print("[CLIENT] Server responded:", r.status_code)
            except Exception as e:
                print("[CLIENT ERROR]", e)
            time.sleep(random.uniform(1, 3))  # interval
        else:
            time.sleep(1)

def listen_control():
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((CONTROL_HOST, CONTROL_PORT))
    while True:
        data = s.recv(1024).decode()
        if not data:
            break
        if data == "START":
            running = True
            print("[*] Client simulation started")
        elif data == "STOP":
            running = False
            print("[*] Client simulation stopped")

if __name__ == "__main__":
    threading.Thread(target=send_requests, daemon=True).start()
    listen_control()
