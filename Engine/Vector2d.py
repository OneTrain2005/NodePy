import math

class Vector2d:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Vector2d):
            return False
        return math.isclose(self.x, o.x, rel_tol=1e-9) and math.isclose(self.y, o.y, rel_tol=1e-9)

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

    def direction_to(self, target: "Vector2d") -> "Vector2d":
        """Returns the normalized vector pointing from self to target."""
        return (target - self).normalized()

    def distance_to(self, o: "Vector2d") -> float:
        """Returns the Euclidean distance between self and another vector."""
        return (o - self).length()

    def distance_squared_to(self, o: "Vector2d") -> float:
        """Returns the squared distance; faster for distance comparisons."""
        return (o.x - self.x)**2 + (o.y - self.y)**2