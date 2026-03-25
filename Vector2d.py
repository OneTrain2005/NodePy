class Vector2d:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other:Vector2d)->Vector2d: return Vector2d(self.x + other.x, self.y + other.y)
    def __sub__(self, other:Vector2d)->Vector2d: return Vector2d(self.x - other.x, self.y - other.y)
