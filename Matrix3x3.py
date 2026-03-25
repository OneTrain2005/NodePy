from __future__ import annotations
import math
from Vector2d import Vector2d

class Matrix3x3:
    def __init__(self, data=None)->None:
        self.m = data if data else [[1,0,0],[0,1,0],[0,0,1]]

    def __mul__(self, other: 'Matrix3x3') -> 'Matrix3x3':
        res = [[0]*3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                res[i][j] = sum(self.m[i][k] * other.m[k][j] for k in range(3))
        return Matrix3x3(res)

    @staticmethod
    def translation(pos: Vector2d) -> 'Matrix3x3':
        return Matrix3x3([
            [1, 0, pos.x],
            [0, 1, pos.y],
            [0, 0, 1]
        ])

    @staticmethod
    def rotation(angle_deg: float) -> 'Matrix3x3':
        rad = math.radians(angle_deg)
        c, s = math.cos(rad), math.sin(rad)
        return Matrix3x3([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])

    @staticmethod
    def scaling(scale: Vector2d) -> 'Matrix3x3':
        return Matrix3x3([
            [scale.x, 0,       0],
            [0,       scale.y, 0],
            [0,       0,       1]
        ])

    @staticmethod
    def make_transform(pos: Vector2d, angle_deg: float, scale: Vector2d) -> 'Matrix3x3':
        # Correct TRS order: T * R * S
        # This means: scale first (in local space), then rotate, then translate.
        # A child's relative_pos is in the parent's LOCAL space (post-rotation,
        # post-scale of parent), which is the standard Godot-style behaviour.
        T = Matrix3x3.translation(pos)
        R = Matrix3x3.rotation(angle_deg)
        S = Matrix3x3.scaling(scale)
        return T * R * S

    def multiply_vec(self, x: float, y: float) -> tuple[float, float]:
        """Applies matrix to a 2D point (homogeneous w=1), returns (x, y)."""
        nx = self.m[0][0]*x + self.m[0][1]*y + self.m[0][2]
        ny = self.m[1][0]*x + self.m[1][1]*y + self.m[1][2]
        w  = self.m[2][0]*x + self.m[2][1]*y + self.m[2][2]
        # Perspective division — safe for all affine transforms (w==1),
        # and correct if a projective matrix is ever introduced.
        if w != 0 and w != 1:
            nx /= w
            ny /= w
        return nx, ny
