from __future__ import annotations

import math
from typing import List, Optional, Tuple

from Engine.Vector2d import Vector2d


class Matrix3x3:
    """
    Immutable-style 3×3 matrix for 2D affine transforms.

    Stored as a row-major list-of-lists ``m`` with the layout::

        | m[0][0]  m[0][1]  m[0][2] |   | a  b  tx |
        | m[1][0]  m[1][1]  m[1][2] | = | c  d  ty |
        | m[2][0]  m[2][1]  m[2][2] |   | 0  0   1 |

    The bottom row is always ``[0, 0, 1]`` for every matrix produced by this
    class (translation, rotation, scaling, make_transform, and their products).
    ``multiply_vec`` and ``__mul__`` rely on this assumption — do not hand-
    construct matrices with a non-affine bottom row.

    Coordinate convention
    ---------------------
    Positive x goes right, positive y goes down (tkinter screen space).
    Angles are in degrees, measured clockwise from the positive x-axis.

    Typical usage
    -------------
    Build a node's local-to-world matrix once per dirty frame via
    ``make_transform``, then concatenate it with the camera view matrix using
    ``*``, and finally project individual points with ``multiply_vec``.
    """

    __slots__ = ("m",)

    def __init__(self, data: Optional[List[List[float]]] = None):
        """
        Parameters
        ----------
        data:
            A 3×3 row-major list-of-lists.  Omit (or pass ``None``) to get
            the identity matrix.
        """
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
        """
        Return the matrix product ``self @ other``.

        Multiplication is applied right-to-left in the transform chain, e.g.::

            world = parent_world * local_trs

        The 27 products are inlined explicitly — no inner loop or generator —
        to avoid per-element allocation overhead at call-rate.
        """
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
        """Return a pure translation matrix that shifts points by ``pos``."""
        return Matrix3x3([[1, 0, pos.x], [0, 1, pos.y], [0, 0, 1]])

    @staticmethod
    def rotation(angle_deg: float) -> "Matrix3x3":
        """
        Return a pure rotation matrix.

        Parameters
        ----------
        angle_deg:
            Clockwise rotation in degrees (positive = clockwise in screen space).
        """
        r = math.radians(angle_deg)
        c, s = math.cos(r), math.sin(r)
        return Matrix3x3([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    @staticmethod
    def scaling(scale: Vector2d) -> "Matrix3x3":
        """Return a pure (non-uniform) scale matrix."""
        return Matrix3x3([[scale.x, 0, 0], [0, scale.y, 0], [0, 0, 1]])

    @staticmethod
    def make_transform(pos: Vector2d, angle_deg: float, scale: Vector2d) -> "Matrix3x3":
        """
        Build a combined TRS (translate-rotate-scale) matrix in one step.

        Equivalent to ``translation(pos) * rotation(angle_deg) * scaling(scale)``
        but computed directly from the closed-form result, avoiding two
        intermediate matrix objects and two full ``__mul__`` calls.

        The resulting matrix is::

            | c*sx  -s*sy  tx |
            | s*sx   c*sy  ty |
            |   0      0    1 |

        where ``c = cos(angle_deg)``, ``s = sin(angle_deg)``,
        ``sx, sy = scale.x, scale.y``, and ``tx, ty = pos.x, pos.y``.
        """
        r = math.radians(angle_deg)
        c, s = math.cos(r), math.sin(r)
        return Matrix3x3([
            [c * scale.x, -s * scale.y, pos.x],
            [s * scale.x,  c * scale.y, pos.y],
            [0.0,           0.0,         1.0  ],
        ])

    def inverse_translate(self) -> "Matrix3x3":
        """
        Return a copy of this matrix with the translation component negated.

        Useful for building a camera view matrix: negate the camera's world-
        space position so the world shifts in the opposite direction on screen.
        Does not invert rotation or scale.
        """
        inv = Matrix3x3([row[:] for row in self.m])
        inv.m[0][2] = -self.m[0][2]
        inv.m[1][2] = -self.m[1][2]
        return inv

    # ── Application ─────────────────────────────────────────────────────────

    def multiply_vec(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform the 2D point ``(x, y)`` by this matrix and return ``(nx, ny)``.

        Assumes the bottom row is ``[0, 0, 1]`` (affine transform), so the
        homogeneous divide is skipped.  All matrices produced by this class
        satisfy that invariant.
        """
        return (
            self.m[0][0] * x + self.m[0][1] * y + self.m[0][2],
            self.m[1][0] * x + self.m[1][1] * y + self.m[1][2],
        )

    def decompose(self) -> Tuple[float, float, float, float, float]:
        """
        Extract ``(tx, ty, rot_deg, scale_x, scale_y)`` from an affine TRS matrix.

        Works by reading the translation column directly and deriving rotation
        and scale from the first two columns::

            scale_x = |column 0| = hypot(m[0][0], m[1][0])
            scale_y = |column 1| = hypot(m[0][1], m[1][1])
            rot_deg = atan2(m[1][0], m[0][0])   (clockwise, degrees)

        Assumes no shear.  Non-uniform scale is handled correctly as long as
        the matrix was built via ``make_transform`` or equivalent TRS chain.

        When applied to ``cam * node.global_matrix`` the camera zoom is folded
        into ``scale_x`` / ``scale_y``, while ``rot_deg`` reflects only the
        node's own rotation (zoom cancels in the atan2).
        """
        tx = self.m[0][2]
        ty = self.m[1][2]
        scale_x = math.hypot(self.m[0][0], self.m[1][0])
        scale_y = math.hypot(self.m[0][1], self.m[1][1])
        rot_deg = math.degrees(math.atan2(self.m[1][0], self.m[0][0]))
        return tx, ty, rot_deg, scale_x, scale_y
