from scapy.all import IP, UDP, send, sniff, wrpcap
import socket
import threading
import random
import string
import time
import json
import uuid

CONTROL_HOST = ("10.10.0.1", 9000)

TARGET_SERVER_IP = "10.10.0.2"
TARGET_SERVER_PORT = 8080

CLIENT_PORT = 10000
CLIENT_ID = str(uuid.uuid4())

simulating = False

def await_ack(sock):
    while True:
        try:
            data, addr = sock.recvfrom(1024)

            packet = json.loads(data)

            if packet["type"] == "ack":
                return True
        except socket.timeout:
            return False
        finally:
            return False

def random_string(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def spoof_traffic():
    global simulating
    
    while True:
        if simulating:
            packet = {"type":"traffic", "data":f"{CLIENT_ID}-{random_string()}"}
            raw_packet = json.dumps(packet)

            rand_ip = random.randint(2, 254)

            ip = IP(src=f"10.10.1.{rand_ip}", dst=TARGET_SERVER_IP)
            udp = UDP(sport=CLIENT_PORT, dport=TARGET_SERVER_PORT)

            spoofed_packet = ip / udp / raw_packet.encode('utf-8')

            print("[*] Sending spoofed packet:")
            spoofed_packet.show()

            send(spoofed_packet)

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

    sock.sendto(raw_begin_packet.encode('utf-8'), CONTROL_HOST)

    # transfer
    with open("capture.pcap", "rb") as f:
        while True:
            chunk = f.read(512)

            if not chunk:
                break

            packet = {"type":"data_segment","data":chunk}
            raw_packet = json.dumps(packet)

            sock.sendto(raw_packet.encode('utf-8'), CONTROL_HOST)

            while True:
                data, addr = sock.recvfrom(1024)

                packet = json.loads(data)

                if packet["type"] == "ack":
                    break

    # end transfer
    end_packet = {"type":"data_end"}
    raw_end_packet = json.dumps(end_packet)

    sock.sendto(raw_end_packet.encode('utf-8'), CONTROL_HOST)

def main():
    global simulating

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", CLIENT_PORT))

    # join control network
    packet = {"type":"join", "role":"adversary"}
    raw_packet = json.dumps(packet)

    sock.settimeout(1)

    while True:
        sock.sendto(raw_packet.encode('utf-8'), CONTROL_HOST)

        print("[*] Joining simulation network...")

        if await_ack(sock):
            break

    print("[*] Joined simulation network")

    # simulation thread
    sim_thread = threading.Thread(target=spoof_traffic, daemon=True)
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

            print(f"[*] Started spoofing traffic to {TARGET_SERVER_IP}:{TARGET_SERVER_PORT}")
        elif packet_type == "stop":
            simulating = False
            send_captures(sock)

            print("[*] Stopped simulating; sent captures to control server")

if __name__ == "__main__":
    main()
