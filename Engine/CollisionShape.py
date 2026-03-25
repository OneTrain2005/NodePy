from __future__ import annotations
from Engine.Node import Node
from Engine.Matrix3x3 import Matrix3x3
from Engine.Vector2d import Vector2d
from Engine.Signal import Signal
from typing import Optional, Tuple, List
import tkinter as tk

class CollisionShape(Node):
    """
    Axis-Aligned Bounding Box (AABB) in world space.

    The AABB is recomputed from the node's global_matrix each time it is
    needed, so it always reflects the current transform.

    Usage
    -----
    cs = CollisionShape("col", width=20, height=20, parent=my_node)

    # check overlap
    if cs.overlaps(other_cs):
        ...

    # check point (e.g. mouse cursor)
    if cs.contains_point(Input._mouse_pos):
        ...

    Signals
    -------
    self.body_entered(other: CollisionShape)
    self.body_exited(other: CollisionShape)
    """

    # Class-level registry so shapes can find each other
    _all: List["CollisionShape"] = []

    def __init__(self, name: str, width: float = 20, height: float = 20,
                 debug_draw: bool = False, parent: Optional[Node] = None):
        super().__init__(name, parent=parent)
        self.width      = width
        self.height     = height
        self.debug_draw = debug_draw

        self.body_entered = Signal("body_entered")
        self.body_exited  = Signal("body_exited")

        self._overlapping: set["CollisionShape"] = set()
        CollisionShape._all.append(self)

    def _ready(self) -> None:
        pass

    def get_aabb(self) -> Tuple[float, float, float, float]:
        """
        Returns (min_x, min_y, max_x, max_y) in world space.
        The AABB wraps all four corners of the local box after transformation,
        so it stays correct under rotation and scale.
        """
        mat  = self.global_matrix
        hw, hh = self.width / 2, self.height / 2
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        xs = []
        ys = []
        for px, py in corners:
            wx, wy = mat.multiply_vec(px, py)
            xs.append(wx)
            ys.append(wy)
        return min(xs), min(ys), max(xs), max(ys)

    def overlaps(self, other: "CollisionShape") -> bool:
        ax0, ay0, ax1, ay1 = self.get_aabb()
        bx0, by0, bx1, by1 = other.get_aabb()
        return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0

    def contains_point(self, point: Vector2d) -> bool:
        x0, y0, x1, y1 = self.get_aabb()
        return x0 <= point.x <= x1 and y0 <= point.y <= y1

    def _update(self, delta: float) -> None:
        # Emit body_entered / body_exited signals
        current: set["CollisionShape"] = set()
        for other in CollisionShape._all:
            if other is self or not other.visible:
                continue
            if self.overlaps(other):
                current.add(other)
                if other not in self._overlapping:
                    self.body_entered.emit(other)
        for exited in self._overlapping - current:
            self.body_exited.emit(exited)
        self._overlapping = current

    def _draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        if not self.debug_draw:
            return
        mat  = cam * self.global_matrix
        hw, hh = self.width / 2, self.height / 2
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        pts = []
        for px, py in corners:
            sx, sy = mat.multiply_vec(px, py)
            pts.extend([sx, sy])
        canvas.create_polygon(pts, fill="", outline="#00ff88",
                              width=1, dash=(4, 3))