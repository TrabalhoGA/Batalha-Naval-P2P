import random

class Board:
    def __init__(self):
        self.grid = [["~" for _ in range(10)] for _ in range(10)]
        self.ships = []

    def place_ship(self, ship):
        self.ships.append(ship)
        for x, y in ship.positions:
            self.grid[y][x] = "S"

    def receive_shot(self, x, y):
        for ship in self.ships:
            if (x, y) in ship.positions:
                ship.hits.add((x, y))
                return "hit" if not ship.is_destroyed() else "destroyed"
        return "miss"