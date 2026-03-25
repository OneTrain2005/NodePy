from __future__ import annotations

from typing import List, Optional
from Vector2d import Vector2d
from Matrix3x3 import Matrix3x3

class Node:
    def __init__(self, name: str, relative_pos: Vector2d, parent: Optional['Node'] = None):
        self.name = name
        self.parent = parent
        self.children: List['Node'] = []
        self._global_matrix = Matrix3x3()
        self._dirty = True

        # Private backing fields — use property setters so any change
        # automatically propagates the dirty flag down the subtree.
        self._relative_pos = relative_pos
        self._rotation = 0.0
        self._scale = Vector2d(1.0, 1.0)

        if parent:
            parent.children.append(self)

    # ---- Properties with automatic invalidation -------------------------

    @property
    def relative_pos(self) -> Vector2d:
        return self._relative_pos

    @relative_pos.setter
    def relative_pos(self, value: Vector2d):
        self._relative_pos = value
        self.invalidate()

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, value: float):
        self._rotation = value
        self.invalidate()

    @property
    def scale(self) -> Vector2d:
        return self._scale

    @scale.setter
    def scale(self, value: Vector2d):
        self._scale = value
        self.invalidate()

    # ---- Transform pipeline ----------------------------------------------

    def invalidate(self):
        """Mark this node and all descendants as needing a transform update."""
        if self._dirty:
            return  # already dirty — subtree already flagged
        self._dirty = True
        for child in self.children:
            child.invalidate()

    def update_transform(self):
        if not self._dirty:
            return
        local = Matrix3x3.make_transform(self._relative_pos, self._rotation, self._scale)
        if self.parent:
            self.parent.update_transform()
            self._global_matrix = self.parent._global_matrix * local
        else:
            self._global_matrix = local
        self._dirty = False

    @property
    def global_matrix(self) -> Matrix3x3:
        self.update_transform()
        return self._global_matrix

    # ---- Convenience: global position ------------------------------------

    @property
    def global_position(self) -> Vector2d:
        gx, gy = self.global_matrix.multiply_vec(0, 0)
        return Vector2d(gx, gy)
