import threading
import socket
from scapy.all import sniff, wrpcap

# Global stop flag for sniffing
stop_sniffing = threading.Event()
pcap_filename = "capture.pcap"

CONTROL_SERVER_IP = "10.10.0.100"  # Set your control server IP here
PCAP_SEND_PORT = 6666              # Must match control server PCAP receive port

def packet_handler(packet):
    print(packet.summary())

def sniff_packets(interface):
    packets = sniff(iface=interface, prn=packet_handler, stop_filter=lambda x: stop_sniffing.is_set())
    # Save packets to PCAP when stopped
    wrpcap(pcap_filename, packets)
    print(f"Capture saved to {pcap_filename}")

def send_pcap_to_server():
    try:
        with socket.create_connection((CONTROL_SERVER_IP, PCAP_SEND_PORT), timeout=10) as sock:
            with open(pcap_filename, 'rb') as f:
                print(f"Sending {pcap_filename} to server...")
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    sock.sendall(chunk)
            print("PCAP file sent successfully.")
    except Exception as e:
        print(f"Failed to send pcap file: {e}")

def tcp_listener(port, interface):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(1)
    print(f"Listening for commands on TCP port {port}...")
    sniffer_thread = None
    while True:
        client, addr = server.accept()
        print(f"Connection from {addr}")
        while True:
            data = client.recv(1024).decode("utf-8").strip().upper()
            if data == "START" and (sniffer_thread is None or not sniffer_thread.is_alive()):
                stop_sniffing.clear()
                sniffer_thread = threading.Thread(target=sniff_packets, args=(interface,))
                sniffer_thread.start()
                client.sendall(b"Started capturing\n")
            elif data == "STOP" and sniffer_thread is not None and sniffer_thread.is_alive():
                stop_sniffing.set()
                sniffer_thread.join()
                # Once stopped, send PCAP to control server
                send_pcap_to_server()
                client.sendall(b"Stopped capturing and sent pcap\n")
            elif data == "EXIT":
                client.sendall(b"Exiting\n")
                client.close()
                server.close()
                return
            else:
                client.sendall(b"Unknown command\n")

if __name__ == "__main__":
    INTERFACE = "eth0"   # Change to your capture interface
    PORT = 5555          # Port for receiving START/STOP commands
    tcp_listener(PORT, INTERFACE)
