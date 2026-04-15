from __future__ import annotations

import math
from typing import List, Optional, Tuple

from Engine.Vector2d import Vector2d


class Matrix3x3:
    __slots__ = ("m",)

    def __init__(self, data: Optional[List[List[float]]] = None):
        self.m: List[List[float]] = (
            data
            if data
            else [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ]
        )

    def __mul__(self, other: "Matrix3x3") -> "Matrix3x3":
        res = [[0.0] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                res[i][j] = sum(self.m[i][k] * other.m[k][j] for k in range(3))
        return Matrix3x3(res)

    # ── Factory methods ──────────────────────────────────────────────────────

    @staticmethod
    def translation(pos: Vector2d) -> "Matrix3x3":
        return Matrix3x3([[1, 0, pos.x], [0, 1, pos.y], [0, 0, 1]])

    @staticmethod
    def rotation(angle_deg: float) -> "Matrix3x3":
        r = math.radians(angle_deg)
        c, s = math.cos(r), math.sin(r)
        return Matrix3x3([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    @staticmethod
    def scaling(scale: Vector2d) -> "Matrix3x3":
        return Matrix3x3([[scale.x, 0, 0], [0, scale.y, 0], [0, 0, 1]])

    @staticmethod
    def make_transform(pos: Vector2d, angle_deg: float, scale: Vector2d) -> "Matrix3x3":
        """Standard TRS: translate * rotate * scale."""
        return (
            Matrix3x3.translation(pos)
            * Matrix3x3.rotation(angle_deg)
            * Matrix3x3.scaling(scale)
        )

    def inverse_translate(self) -> "Matrix3x3":
        """Returns a matrix that undoes only the translation component.
        Useful for camera: negate world-space offset."""
        inv = Matrix3x3([row[:] for row in self.m])
        inv.m[0][2] = -self.m[0][2]
        inv.m[1][2] = -self.m[1][2]
        return inv

    # ── Application ─────────────────────────────────────────────────────────

    def multiply_vec(self, x: float, y: float) -> Tuple[float, float]:
        """Transform a 2D point (w=1) through this matrix."""
        nx = self.m[0][0] * x + self.m[0][1] * y + self.m[0][2]
        ny = self.m[1][0] * x + self.m[1][1] * y + self.m[1][2]
        w = self.m[2][0] * x + self.m[2][1] * y + self.m[2][2]
        if w not in (0.0, 1.0):
            nx /= w
            ny /= w
        return nx, ny
