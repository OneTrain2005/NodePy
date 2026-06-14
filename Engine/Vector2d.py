from __future__ import annotations
import math


class Vector2d:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)

    # Comparison
    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Vector2d):
            return False
        return math.isclose(self.x, o.x, rel_tol=1e-9) and math.isclose(self.y, o.y, rel_tol=1e-9)

    # Arithmetic
    def __add__(self, o: Vector2d) -> Vector2d:
        if not isinstance(o, Vector2d):
            return NotImplemented
        return Vector2d(self.x + o.x, self.y + o.y)

    def __sub__(self, o: Vector2d) -> Vector2d:
        if not isinstance(o, Vector2d):
            return NotImplemented
        return Vector2d(self.x - o.x, self.y - o.y)

    def __neg__(self) -> Vector2d:
        return Vector2d(-self.x, -self.y)

    def __mul__(self, o: float | Vector2d) -> Vector2d:
        if isinstance(o, Vector2d):
            # Hadamard (component-wise) product
            return Vector2d(self.x * o.x, self.y * o.y)
        if isinstance(o, (int, float)):
            return Vector2d(self.x * o, self.y * o)
        return NotImplemented

    def __rmul__(self, o: float) -> Vector2d:
        return self.__mul__(o)

    def __truediv__(self, o: float) -> Vector2d:
        if not isinstance(o, (int, float)):
            return NotImplemented
        return Vector2d(self.x / o, self.y / o)

    def __floordiv__(self, o: float) -> Vector2d:
        if not isinstance(o, (int, float)):
            return NotImplemented
        return Vector2d(self.x // o, self.y // o)

    def __abs__(self) -> float:
        return self.length()

    # Representation
    def __repr__(self) -> str:
        return f"Vector2d({self.x:.2f}, {self.y:.2f})"

    def __iter__(self):
        yield self.x
        yield self.y

    # Vector operations
    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> Vector2d:
        n = self.length()
        return Vector2d(self.x / n, self.y / n) if n else Vector2d()

    def dot(self, o: Vector2d) -> float:
        return self.x * o.x + self.y * o.y

    # syntax sugar for dot
    def __matmul__(self, o: Vector2d) -> float:
        return self.dot(o)

    def direction_to(self, target: Vector2d) -> Vector2d:
        return (target - self).normalized()

    def distance_to(self, o: Vector2d) -> float:
        return (o - self).length()

    def distance_squared_to(self, o: Vector2d) -> float:
        dx = o.x - self.x
        dy = o.y - self.y
        return dx * dx + dy * dy