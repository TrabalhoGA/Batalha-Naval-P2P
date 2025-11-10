import socket
import threading
from connection import Connection

class TCPConnection(Connection):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.listen()

    def send(self, message: str, target_ip: str, target_port: int):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_ip, target_port))
            s.sendall(message.encode())

    def listen(self, callback):
        def _listen():
            while True:
                conn, addr = self.sock.accept()
                data = conn.recv(1024)
                callback(data.decode(), addr)
                conn.close()
        threading.Thread(target=_listen, daemon=True).start()
