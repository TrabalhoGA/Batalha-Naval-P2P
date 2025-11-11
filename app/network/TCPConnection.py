import socket
import threading
from app.network.connection import Connection

class TCPConnection(Connection):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(5)

    def send(self, message: str, target_ip: str, target_port: int):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((target_ip, target_port))
                s.sendall(message.encode())
        except Exception as e:
            print(f"[ERRO TCP] Falha ao enviar mensagem para {target_ip}: {e}")

    def listen(self, callback):
        def _listen():
            while True:
                try:
                    conn, addr = self.sock.accept()
                    data = conn.recv(1024)
                    if data:
                        callback(data.decode(), addr)
                    conn.close()
                except Exception as e:
                    print(f"[ERRO TCP] Erro ao aceitar conexão: {e}")
        threading.Thread(target=_listen, daemon=True).start()

    def sendto(self, message: bytes, target: tuple):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(target)
                s.sendall(message)
        except Exception as e:
            print(f"[ERRO TCP] Falha ao enviar mensagem: {e}")

    