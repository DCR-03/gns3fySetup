import socket
import threading
import json
from scapy.all import sniff, wrpcap

CONTROL_HOST = ("10.10.0.1", 9000)
PORT = 8080

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
    sock.bind(("0.0.0.0", PORT))

    # join control network
    packet = {"type":"join", "role":"server"}
    raw_packet = json.dumps(packet)

    sock.settimeout(1)

    while True:
        sock.sendto(raw_packet.encode('utf-8'), CONTROL_HOST)

        print("[*] Joining simulation network...")

        if await_ack(sock):
            break

    print("[*] Joined simulation network")

    # capture thread
    capture_thread = threading.Thread(target=capture_traffic, daemon=True)
    capture_thread.start()

    while True:
        data, addr = sock.recvfrom(1024)

        packet = json.loads(data)
        packet_type = packet["type"]

        if packet_type == "start" and not simulating:
            simulating = True

            print("[*] Started listening for simulation traffic")
        elif packet_type == "stop" and simulating:
            simulating = False
            send_captures(sock)

            print("[*] Stopped simulating; sent captures to control server")
        elif packet_type == "traffic" and simulating:
            packet = {"type":"echo", "data":packet["data"]}
            raw_packet = json.dumps(packet)

            sock.sendto(raw_packet.encode('utf-8'), addr)

if __name__ == "__main__":
    main()
