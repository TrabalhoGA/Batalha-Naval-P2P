from TCPConnection import TCPConnection
from UDPConnection import UDPConnection

class PeerService:
    def __init__(self):
        self.peers = set()

    def add_peer(self, ip):
        self.peers.add(ip)

    def remove_peer(self, ip):
        self.peers.discard(ip)
