from __future__ import annotations

from typing import List, Optional
from Engine.Vector2d import Vector2d
from Engine.Matrix3x3 import Matrix3x3
from Engine.Signal import Signal
import tkinter as tk

class Node:
    """
    Base scene-graph node.

    Lifecycle
    ---------
    _ready()          Called once when the node is added to an active tree.
    _update(delta)    Called every frame before drawing.
    _draw(canvas, camera_matrix)
                      Called every frame; override to draw custom shapes.

    Signals (built-in)
    ------------------
    self.tree_entered   emitted when added to tree
    self.tree_exited    emitted when removed from tree
    """

    def __init__(self, name: str, relative_pos: Optional[Vector2d] = None,
                 parent: Optional["Node"] = None):
        self.name = name
        self.parent: Optional["Node"] = None
        self.children: List["Node"] = []
        self._global_matrix = Matrix3x3()
        self._dirty = True
        self._ready_called = False

        # Built-in signals
        self.tree_entered = Signal("tree_entered")
        self.tree_exited  = Signal("tree_exited")

        # Backing fields — written through properties so changes auto-invalidate
        self._relative_pos = relative_pos or Vector2d()
        self._rotation     = 0.0
        self._scale        = Vector2d(1.0, 1.0)

        # Visibility
        self.visible = True

        if parent is not None:
            parent.add_child(self)

    # ── Tree management ──────────────────────────────────────────────────────

    def add_child(self, child: "Node") -> "Node":
        if child.parent is not None:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)
        child.invalidate()
        if self._ready_called and not child._ready_called:
            child._call_ready()
        child.tree_entered.emit(child)
        return child

    def remove_child(self, child: "Node") -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            child.tree_exited.emit(child)

    def get_child(self, name: str) -> Optional["Node"]:
        for c in self.children:
            if c.name == name:
                return c
        return None

    # ── Properties with auto-invalidation ───────────────────────────────────

    @property
    def relative_pos(self) -> Vector2d:
        return self._relative_pos

    @relative_pos.setter
    def relative_pos(self, value: Vector2d) -> None:
        self._relative_pos = value
        self.invalidate()

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, value: float) -> None:
        self._rotation = value
        self.invalidate()

    @property
    def scale(self) -> Vector2d:
        return self._scale

    @scale.setter
    def scale(self, value: Vector2d) -> None:
        self._scale = value
        self.invalidate()

    # ── Transform pipeline ───────────────────────────────────────────────────

    def invalidate(self) -> None:
        if self._dirty:
            return
        self._dirty = True
        for child in self.children:
            child.invalidate()

    def update_transform(self) -> None:
        if not self._dirty:
            return
        local = Matrix3x3.make_transform(
            self._relative_pos, self._rotation, self._scale
        )
        if self.parent is not None:
            self.parent.update_transform()
            self._global_matrix = self.parent._global_matrix * local
        else:
            self._global_matrix = local
        self._dirty = False

    @property
    def global_matrix(self) -> Matrix3x3:
        self.update_transform()
        return self._global_matrix

    @property
    def global_position(self) -> Vector2d:
        gx, gy = self.global_matrix.multiply_vec(0, 0)
        return Vector2d(gx, gy)

    # ── Lifecycle hooks (override in subclasses) ─────────────────────────────

    def _call_ready(self) -> None:
        self._ready_called = True
        self._ready()
        for child in self.children:
            if not child._ready_called:
                child._call_ready()

    def _ready(self) -> None:
        """Override: called once when node enters the active tree."""

    def _update(self, delta: float) -> None:
        """Override: called every frame with elapsed seconds."""

    def _draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        """Override: called every frame for custom drawing."""

    # ── Internal frame dispatch ──────────────────────────────────────────────

    def _process(self, delta: float) -> None:
        if not self.visible:
            return
        self._update(delta)
        for child in self.children:
            child._process(delta)

    def _render(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        if not self.visible:
            return
        self._draw(canvas, cam)
        for child in self.children:
            child._render(canvas, cam)
