import math

class Vector2d:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __add__(self, o: "Vector2d") -> "Vector2d":
        return Vector2d(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vector2d") -> "Vector2d":
        return Vector2d(self.x - o.x, self.y - o.y)

    def __mul__(self, scalar: float) -> "Vector2d":
        return Vector2d(self.x * scalar, self.y * scalar)

    def __repr__(self) -> str:
        return f"Vector2d({self.x:.2f}, {self.y:.2f})"

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vector2d":
        n = self.length()
        return Vector2d(self.x / n, self.y / n) if n else Vector2d()

    def dot(self, o: "Vector2d") -> float:
        return self.x * o.x + self.y * o.y
