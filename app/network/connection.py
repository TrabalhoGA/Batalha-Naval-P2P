# app/network/connection.py

class Connection:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def send(self, message: str, target_ip: str, target_port: int):
        raise NotImplementedError

    def listen(self):
        raise NotImplementedError

    def sendto(self, message: bytes, target: tuple):
        raise NotImplementedError