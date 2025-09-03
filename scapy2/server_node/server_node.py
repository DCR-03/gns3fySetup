# server_node.py
import socket
import threading
import http.server
import socketserver

CONTROL_HOST = "10.10.0.1"  # Control server IP
CONTROL_PORT = 9000
HTTP_PORT = 8080

running = False

class EchoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global running
        if not running:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"Simulation not running")
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(self.path.encode())

def http_server():
    with socketserver.TCPServer(("", HTTP_PORT), EchoHandler) as httpd:
        print(f"[+] ServerNode listening HTTP on {HTTP_PORT}")
        httpd.serve_forever()

def listen_control():
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((CONTROL_HOST, CONTROL_PORT))
    while True:
        data = s.recv(1024).decode()
        if not data:
            break
        if data == "START":
            running = True
            print("[*] Simulation started")
        elif data == "STOP":
            running = False
            print("[*] Simulation stopped")
        elif data == "COLLECT":
            print("[*] Would collect pcap files here")

if __name__ == "__main__":
    threading.Thread(target=http_server, daemon=True).start()
    listen_control()
