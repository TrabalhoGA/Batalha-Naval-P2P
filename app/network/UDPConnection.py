import socket
import threading
from app.network.connection import Connection

class UDPConnection(Connection):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((ip, port))

    def send(self, message: str, target_ip: str, target_port: int):
        try:
            self.sock.sendto(message.encode(), (target_ip, target_port))
        except Exception as e:
            print(f"[ERRO UDP] Falha ao enviar mensagem: {e}")

    def listen(self, callback):
        def _listen():
            while True:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    callback(data.decode(), addr)
                except Exception as e:
                    print(f"[ERRO UDP] Erro ao receber dados: {e}")
        threading.Thread(target=_listen, daemon=True).start()

    def sendto(self, message: bytes, target: tuple):
        try:
            self.sock.sendto(message, target)
        except Exception as e:
            print(f"[ERRO UDP] Falha ao enviar mensagem: {e}")

