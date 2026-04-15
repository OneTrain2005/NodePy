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
        a, b = self.m, other.m
        return Matrix3x3([
            [a[0][0]*b[0][0] + a[0][1]*b[1][0] + a[0][2]*b[2][0],
             a[0][0]*b[0][1] + a[0][1]*b[1][1] + a[0][2]*b[2][1],
             a[0][0]*b[0][2] + a[0][1]*b[1][2] + a[0][2]*b[2][2]],
            [a[1][0]*b[0][0] + a[1][1]*b[1][0] + a[1][2]*b[2][0],
             a[1][0]*b[0][1] + a[1][1]*b[1][1] + a[1][2]*b[2][1],
             a[1][0]*b[0][2] + a[1][1]*b[1][2] + a[1][2]*b[2][2]],
            [a[2][0]*b[0][0] + a[2][1]*b[1][0] + a[2][2]*b[2][0],
             a[2][0]*b[0][1] + a[2][1]*b[1][1] + a[2][2]*b[2][1],
             a[2][0]*b[0][2] + a[2][1]*b[1][2] + a[2][2]*b[2][2]],
        ])

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
        """Standard TRS computed directly — avoids two intermediate matrix multiplications."""
        r = math.radians(angle_deg)
        c, s = math.cos(r), math.sin(r)
        return Matrix3x3([
            [c * scale.x, -s * scale.y, pos.x],
            [s * scale.x,  c * scale.y, pos.y],
            [0.0,           0.0,         1.0  ],
        ])

    def inverse_translate(self) -> "Matrix3x3":
        """Returns a matrix that undoes only the translation component.
        Useful for camera: negate world-space offset."""
        inv = Matrix3x3([row[:] for row in self.m])
        inv.m[0][2] = -self.m[0][2]
        inv.m[1][2] = -self.m[1][2]
        return inv

    # ── Application ─────────────────────────────────────────────────────────

    def multiply_vec(self, x: float, y: float) -> Tuple[float, float]:
        """Transform a 2D point through this matrix. Assumes affine (bottom row = [0, 0, 1])."""
        return (
            self.m[0][0] * x + self.m[0][1] * y + self.m[0][2],
            self.m[1][0] * x + self.m[1][1] * y + self.m[1][2],
        )
