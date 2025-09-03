# router.py
from scapy.all import sniff, wrpcap

CONTROL_HOST = "10.10.0.1"
CONTROL_PORT = 9000
OUTPUT_PCAP = "captures/router_capture.pcap"

running = False
packets = []

def packet_handler(pkt):
    if running and pkt.haslayer("IP") and (pkt.haslayer("TCP") or pkt.haslayer("ARP")):
        packets.append(pkt)

def start_sniff():
    sniff(prn=packet_handler, store=False)

def control_listener():
    import socket
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((CONTROL_HOST, CONTROL_PORT))
    while True:
        cmd = s.recv(1024).decode()
        if not cmd:
            break
        if cmd == "START":
            running = True
            print("[*] Capture started")
        elif cmd == "STOP":
            running = False
            print("[*] Capture stopped")
        elif cmd == "COLLECT":
            wrpcap(OUTPUT_PCAP, packets)
            print(f"[*] Saved pcap to {OUTPUT_PCAP}")

if __name__ == "__main__":
    import threading
    threading.Thread(target=start_sniff, daemon=True).start()
    control_listener()

