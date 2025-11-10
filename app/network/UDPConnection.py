import socket
import threading
from connection import Connection

class UDPConnection(Connection):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))

    def send(self, message: str, target_ip: str, target_port: int):
        self.sock.sendto(message.encode(), (target_ip, target_port))

    def listen(self, callback):
        def _listen():
            while True:
                data, addr = self.sock.recvfrom(1024)
                callback(data.decode(), addr)
        threading.Thread(target=_listen, daemon=True).start()
