import socket
import threading
import datetime
import json
import os

PORT = 9000
DATA_DIR = "data"

clients = {}

simulating = False
current_sim = None

def broadcast(sock, packet):
    raw_packet = json.dumps(packet)

    for addr in clients:
        sock.sendto(raw_packet, addr)

def send_ack(sock, addr):
    packet = {"type": "ack"}
    raw_packet = json.dumps(packet)
    
    sock.sendto(raw_packet, addr)

def server(sock):
    while True:
        data, addr = sock.recvfrom(1024)

        packet = json.loads(data)
        packet_type = packet["type"]

        if packet_type == "join":
            clients[addr] = {"role":packet["role"]}

            print(f"[+] Node {addr} joined")

            send_ack(sock, addr)
        elif packet_type == "leave":
            del clients[addr]

            print(f"[-] Node {addr} left")
        elif packet_type == "data_begin":
            role = clients[addr]["role"]

            file_path = f"{current_sim}/{role}-{addr}.pcap"
            dir_path = os.path.dirname(file_path)

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            clients[addr]["data_stream"] = open(file_path, "w")

            send_ack(sock, addr)
        elif packet_type == "data_segment":
            stream = clients[addr]["data_stream"]
            data = packet["data"]

            stream.write(data)

            send_ack(sock, addr)
        elif packet_type == "data_end":
            stream = clients[addr]["data_stream"]
            stream.close()

            del clients[addr]["data_stream"]

            send_ack(sock, addr)

def main():
    global simulating
    global current_sim
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))

    server_thread = threading.Thread(target=server, args=(sock,), daemon=True)
    server_thread.start()

    print(f"[*] Listening for connections on 0.0.0.0:{PORT}")

    while True:
        cmd = input("[!] Enter a command (start/stop): ")

        packet = {"type": cmd}

        if cmd == "start" and not simulating:
            simulating = True
            current_sim = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")

            print(f"[*] Started simulation at {current_sim}")
        elif cmd == "stop" and simulating:
            simulating = False
            
            print(f"[*] Stopped simulation; collecting data into ./{current_sim}/")

        broadcast(sock, packet)

if __name__ == "__main__":
    main()
