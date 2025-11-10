import random

class Ship:
    def __init__(self, name, size, positions=None):
        self.name = name
        self.size = size
        self.positions = positions or []
        self.hits = set()

    def is_destroyed(self):
        return len(self.hits) == self.size
