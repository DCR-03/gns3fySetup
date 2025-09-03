# control_server.py
import socket
import threading

HOST = "0.0.0.0"
PORT = 9000
clients = []

def handle_client(conn, addr):
    print(f"[+] Node connected: {addr}")
    clients.append(conn)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"[{addr}] {data.decode()}")
    except:
        pass
    finally:
        clients.remove(conn)
        conn.close()

def broadcast_command(cmd: str):
    print(f"[*] Sending command: {cmd}")
    for conn in clients:
        try:
            conn.sendall(cmd.encode())
        except:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[+] Control server running on {HOST}:{PORT}")

    threading.Thread(target=accept_loop, args=(server,), daemon=True).start()

    while True:
        cmd = input("Enter command (START/STOP/COLLECT/EXIT): ").strip().upper()
        if cmd == "EXIT":
            break
        broadcast_command(cmd)

def accept_loop(server):
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
