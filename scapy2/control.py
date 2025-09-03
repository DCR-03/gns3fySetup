# control_client.py
import socket

CONTROL_SERVER_IP = "127.0.0.1"   # Change to actual server container IP/name in Docker/GNS3
CONTROL_SERVER_PORT = 9000

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((CONTROL_SERVER_IP, CONTROL_SERVER_PORT))
    print(f"[+] Connected to control server at {CONTROL_SERVER_IP}:{CONTROL_SERVER_PORT}")
    try:
        while True:
            cmd = input("Enter command (START/STOP/COLLECT/EXIT): ").strip().upper()
            if cmd == "EXIT":
                break
            s.sendall(cmd.encode())
    finally:
        s.close()

if __name__ == "__main__":
    main()
