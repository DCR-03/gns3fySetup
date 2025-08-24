import socket
import threading
import os

COMMAND_PORT = 5555    # The port your Scapy script listens on for commands
PCAP_RECEIVE_PORT = 6666  # Port to receive PCAP files from clients

def send_command(ip, command):
    try:
        with socket.create_connection((ip, COMMAND_PORT), timeout=5) as sock:
            sock.sendall(command.encode() + b"\n")
            response = sock.recv(1024).decode()
            print(f"Response from {ip}: {response.strip()}")
    except Exception as e:
        print(f"Error sending to {ip}: {e}")

def broadcast_command(ip_list_file, command):
    with open(ip_list_file, 'r') as f:
        ips = [line.strip() for line in f if line.strip()]
    threads = []
    for ip in ips:
        t = threading.Thread(target=send_command, args=(ip, command))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def handle_pcap_client(conn, addr):
    ip = addr[0]
    print(f"Receiving PCAP from {ip}")
    filename = f"capture_{ip.replace('.', '_')}.pcap"
    with open(filename, 'wb') as f:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            f.write(data)
    print(f"Saved capture from {ip} as {filename}")
    conn.close()

def start_pcap_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', PCAP_RECEIVE_PORT))
    server.listen(5)
    print(f"PCAP Receive Server listening on port {PCAP_RECEIVE_PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_pcap_client, args=(conn, addr)).start()

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Control server for distributed Scapy capture.")
    parser.add_argument("--ips", required=True, help="File containing list of client IPs")
    parser.add_argument("--command", required=True, choices=["START", "STOP"], help="Command to send to all clients")

    args = parser.parse_args()

    # Start PCAP receive server thread
    threading.Thread(target=start_pcap_server, daemon=True).start()

    # Broadcast command to clients
    broadcast_command(args.ips, args.command)

    print("Commands sent. PCAP server running. Press Ctrl+C to exit.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Exiting control server.")
        sys.exit()
