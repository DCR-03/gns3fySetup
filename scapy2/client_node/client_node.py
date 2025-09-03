import socket
import threading
import time
import uuid
import random
import string
import json
from scapy.all import sniff, wrpcap

CONTROL_HOST = "10.10.0.1:9000"
SERVER_HOST = "10.10.0.2:8080"

CLIENT_PORT = 9000
CLIENT_ID = str(uuid.uuid4())

simulating = False

def random_string(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def simulate_traffic(sock):
    global simulating
    
    while True:
        if simulating:
            packet = {"type":"traffic", "data":f"{CLIENT_ID}-{random_string()}"}
            raw_packet = json.dumps(packet)
            
            sock.sendto(raw_packet, SERVER_HOST)

            print("[*] Sent traffic")

            wait_time = random.randint(2,4)

            print(f"[*] Sleeping for {wait_time} seconds...")

            time.sleep(random.randint(2,4))

def capture_traffic():
    global simulating
    
    while True:
        if simulating:
            packet_filter = "udp or arp"

            packets = sniff(filter=packet_filter, iface="eth0", timeout=30)
            wrpcap("capture.pcap", packets)

def send_captures(sock):
    # begin transfer
    begin_packet = {"type":"data_begin"}
    raw_begin_packet = json.dumps(begin_packet)

    sock.sendto(raw_begin_packet, CONTROL_HOST)

    # transfer
    with open("capture.pcap", "rb") as f:
        while True:
            chunk = f.read(512)

            if not chunk:
                break

            packet = {"type":"data_segment","data":chunk}
            raw_packet = json.dumps(packet)

            sock.sendto(raw_packet, CONTROL_HOST)

            while True:
                data, addr = sock.recvfrom(1024)

                packet = json.loads(data)

                if packet["type"] == "ack":
                    break

    # end transfer
    end_packet = {"type":"data_end"}
    raw_end_packet = json.dumps(end_packet)

    sock.sendto(raw_end_packet, CONTROL_HOST)

def main():
    global simulating
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", CLIENT_PORT))

    # join control network
    packet = {"type":"join", "role":"client"}
    raw_packet = json.dumps(packet)

    sock.sendto(raw_packet, CONTROL_HOST)

    # simulation thread
    sim_thread = threading.Thread(target=simulate_traffic, args=(sock,), daemon=True)
    sim_thread.start()

    # capture thread
    capture_thread = threading.Thread(target=capture_traffic, daemon=True)
    capture_thread.start()

    while True:
        data, addr = sock.recvfrom(1024)

        packet = json.loads(data)
        packet_type = packet["type"]

        if packet_type == "start":
            simulating = True

            print(f"[*] Started simulating traffic to {SERVER_HOST}")
        elif packet_type == "stop":
            simulating = False
            send_captures(sock)

            print("[*] Stopped simulating; sent captures to control server")

if __name__ == "__main__":
    main()
