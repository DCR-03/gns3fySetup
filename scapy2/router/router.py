# router.py
import socket
import threading
import json
import base64
import io

from scapy.all import sniff, wrpcap

# --- Configuration ---
# IP of the machine running the controller script
CONTROL_HOST = "127.0.0.1"
CONTROL_PORT = 9000
# --- End Configuration ---

# Global variables to manage state
running = False
packets = []
# A lock to safely access the 'packets' list from multiple threads
packet_lock = threading.Lock()

def packet_handler(pkt):
    """
    This function is called by Scapy for each captured packet.
    If capturing is active, it adds the packet to our list.
    """
    if running:
        with packet_lock:
            packets.append(pkt)

def start_sniff():
    """
    Starts the Scapy packet sniffer in a background thread.
    The filter is more efficient than checking packet types in Python.
    """
    sniff(prn=packet_handler, store=False, filter="ip or arp")

def send_capture_data(sock, server_address):
    """
    Handles the process of sending the captured packet data to the controller.
    """
    print("[*] Preparing to send captured data to the controller...")

    with packet_lock:
        if not packets:
            print("[!] No packets were captured. Nothing to send.")
            return
        
        # Use an in-memory binary stream to temporarily hold the .pcap file
        in_memory_capture = io.BytesIO()
        wrpcap(in_memory_capture, packets)
        in_memory_capture.seek(0)  # Rewind to the beginning of the stream to read
        pcap_data = in_memory_capture.read()
        packets.clear() # Clear the global list for the next simulation

    # This helper function sends a JSON packet and waits for an 'ack' response
    def send_and_wait_for_ack(packet_to_send):
        raw_packet = json.dumps(packet_to_send).encode('utf-8')
        sock.sendto(raw_packet, server_address)
        try:
            # Set a timeout to prevent waiting forever
            sock.settimeout(5.0)
            data, _ = sock.recvfrom(1024)
            ack = json.loads(data.decode('utf-8'))
            return ack.get("type") == "ack"
        except socket.timeout:
            print("[!] Error: Timed out waiting for ACK from the controller.")
            return False
        finally:
            sock.settimeout(None) # Disable the timeout

    # 1. Send 'data_begin' to initiate the transfer
    if not send_and_wait_for_ack({"type": "data_begin"}):
        print("[!] Controller did not acknowledge data transfer start. Aborting.")
        return
    print("[*] Controller acknowledged data transfer start.")

    # 2. Base64-encode the binary pcap data to safely send it within a JSON object.
    encoded_data = base64.b64encode(pcap_data).decode('ascii')
    
    # 3. Send the data in small chunks (segments)
    CHUNK_SIZE = 512  # Send 512 bytes of the encoded string at a time
    for i in range(0, len(encoded_data), CHUNK_SIZE):
        chunk = encoded_data[i:i+CHUNK_SIZE]
        segment_packet = {"type": "data_segment", "data": chunk}
        if not send_and_wait_for_ack(segment_packet):
            print("[!] Failed to send a data segment. Aborting.")
            return

    # 4. Send 'data_end' to finalize the transfer
    if send_and_wait_for_ack({"type": "data_end"}):
        print("[+] Successfully sent all capture data to the controller.")
    else:
        print("[!] Controller did not acknowledge data transfer end.")

def control_listener():
    """
    Listens for UDP commands from the controller to start/stop the capture.
    """
    global running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (CONTROL_HOST, CONTROL_PORT)

    # Announce presence to the controller by sending a "join" packet
    join_packet = {"type": "join", "role": "router"}
    sock.sendto(json.dumps(join_packet).encode('utf-8'), server_address)
    print(f"[*] Router node has joined the controller at {CONTROL_HOST}:{CONTROL_PORT}")

    # Listen indefinitely for commands
    while True:
        data, _ = sock.recvfrom(1024)
        packet = json.loads(data.decode('utf-8'))
        command = packet.get("type")

        if command == "start" and not running:
            running = True
            with packet_lock:
                packets.clear()  # Clear any old packets before starting
            print("\n[+] Received START command. Packet capture initiated.")

        elif command == "stop" and running:
            running = False
            print("\n[-] Received STOP command. Packet capture halted.")
            # When capture stops, send the collected data to the controller
            send_capture_data(sock, server_address)

if __name__ == "__main__":
    # Start the packet sniffer in a background thread
    sniffer_thread = threading.Thread(target=start_sniff, daemon=True)
    sniffer_thread.start()

    # Use the main thread to listen for commands from the controller
    control_listener()
