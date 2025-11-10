import random

class GameController:
    def __init__(self, tcp, udp, peers, board):
        self.tcp = tcp
        self.udp = udp
        self.peers = peers
        self.board = board
        self.score = {"hits": 0, "got_hit": 0}

    def handle_shot(self, addr, x, y):
        result = self.board.receive_shot(x, y)
        if result in ["hit", "destroyed"]:
            self.tcp.send(result, addr[0], 5001)
        print(f"Tiro recebido de {addr}: {result}")

    def send_random_shot(self):
        import random
        x, y = random.randint(0, 9), random.randint(0, 9)
        for peer in self.peers.all():
            self.udp.send(f"shot:{x},{y}", peer, 5000)
