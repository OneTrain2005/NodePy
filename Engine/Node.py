from __future__ import annotations

from typing import Any, List, Optional, Tuple
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

    _deferred_free_queue: List["Node"] = []
    _deferred_call_queue: List[Tuple["Node", str, tuple, dict]] = []

    def __init__(self, name: str, relative_pos: Optional[Vector2d] = None,
                 parent: Optional["Node"] = None):
        self.name = name
        self.parent: Optional["Node"] = None
        self.children: List["Node"] = []
        self._global_matrix = Matrix3x3()
        self._dirty = True
        self._ready_called = False
        self._queued_for_free = False
        self._canvas_ids: List[int] = []

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
        if child._queued_for_free:
            raise RuntimeError(
                f"Cannot add node {child.name!r} to tree: it is queued for freeing"
            )
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
            child._propagate_tree_exited()

    def call_deferred(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Queue a method call to run at the end of the current frame."""
        Node._deferred_call_queue.append((self, method_name, args, kwargs))

    @classmethod
    def _flush_deferred_calls(cls) -> None:
        """Execute all queued deferred calls.
        Skips nodes that have been queued for freeing (matches Godot behaviour)."""
        if not cls._deferred_call_queue:
            return
        batch = list(cls._deferred_call_queue)
        cls._deferred_call_queue.clear()
        for node, method_name, args, kwargs in batch:
            if node._queued_for_free:
                continue
            try:
                method = getattr(node, method_name)
                method(*args, **kwargs)
            except Exception:
                import traceback
                traceback.print_exc()

    def queue_free(self) -> None:
        """Queue this node (and all its children) for deletion at the end of the frame."""
        if not self._queued_for_free:
            self._queued_for_free = True
            Node._deferred_free_queue.append(self)
            # Propagate to descendants so they can check their status before the frame ends
            self._propagate_queued_for_free()

    def _propagate_queued_for_free(self) -> None:
        for child in self.children:
            if not child._queued_for_free:
                child._queued_for_free = True
                child._propagate_queued_for_free()

    def _propagate_tree_exited(self) -> None:
        """Emit tree_exited bottom-up on self and all descendants.
        Also clears canvas items so nothing stays stuck on screen."""
        for c in list(self.children):
            c._propagate_tree_exited()
        self.tree_exited.emit(self)
        self._clear_canvas_items()

    def _perform_free(self) -> None:
        """Actually remove this node and its descendants from the tree."""
        if not self._queued_for_free:
            return
        self._queued_for_free = False
        for child in list(self.children):
            child._queued_for_free = True
            child._perform_free()
        if self.parent is not None:
            self.parent.children.remove(self)
            self.parent = None
        self._propagate_tree_exited()

    def get_child(self, name: str) -> Optional["Node"]:
        for c in self.children:
            if c.name == name:
                return c
        return None

    # ── Container sugars ─────────────────────────────────────────────────────

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.children[key]
        if isinstance(key, str):
            child = self.get_child(key)
            if child is None:
                raise KeyError(f"Node {self.name!r} has no child named {key!r}")
            return child
        raise TypeError(f"Node indices must be int or str, not {type(key).__name__}")

    def __iter__(self):
        return iter(self.children)

    def __len__(self) -> int:
        return len(self.children)

    def __contains__(self, item):
        if isinstance(item, Node):
            return item in self.children
        if isinstance(item, str):
            return self.get_child(item) is not None
        return False

    def __bool__(self) -> bool:
        # A node is always truthy regardless of child count.
        # Without this, Python falls back to __len__ for truthiness,
        # making empty nodes unexpectedly falsy.
        return True

    def __iadd__(self, child: "Node") -> "Node":
        self.add_child(child)
        return self

    def __isub__(self, child: "Node") -> "Node":
        self.remove_child(child)
        return self

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
        self._on_invalidate()
        for child in self.children:
            child.invalidate()

    def _on_invalidate(self) -> None:
        """Hook for subclasses to react to transform changes.
        Called whenever relative_pos, rotation, or scale changes."""
        pass

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

    def _update_transform_tree(self) -> None:
        """One-shot top-down transform recalculation. Called by GameLoop before rendering."""
        if self._dirty:
            local = Matrix3x3.make_transform(
                self._relative_pos, self._rotation, self._scale
            )
            if self.parent is not None:
                self._global_matrix = self.parent._global_matrix * local
            else:
                self._global_matrix = local
            self._dirty = False
        for child in self.children:
            child._update_transform_tree()

    @property
    def global_matrix(self) -> Matrix3x3:
        self.update_transform()
        return self._global_matrix

    @property
    def global_position(self) -> Vector2d:
        gx, gy = self.global_matrix.multiply_vec(0, 0)
        return Vector2d(gx, gy)

    def is_on_screen(self, cam: Matrix3x3, margin: float = 0) -> bool:
        from Engine.Camera2D import Camera2D
        active = Camera2D._active
        if active is None:
            return True
        wx, wy = self.global_matrix.multiply_vec(0.0, 0.0)
        sx, sy = cam.multiply_vec(wx, wy)
        vw, vh = active.viewport_w, active.viewport_h
        return not (sx + margin < 0 or sx - margin > vw or
                    sy + margin < 0 or sy - margin > vh)

    # ── Lifecycle hooks (override in subclasses) ─────────────────────────────

    def _call_ready(self) -> None:
        self._ready_called = True
        self._ready()
        for child in self.children:
            if not child._ready_called:
                child._call_ready()

    def _ready(self) -> None:
        """Override: called once when node enters the active tree."""

    def _process(self, delta: float) -> None:
        """Override: called every frame with elapsed seconds. Use for visual updates, animation, and input response."""

    def _physics_process(self, delta: float) -> None:
        """Override: called at fixed timestep. Use for movement, collision, and physics logic."""

    def _update(self, delta: float) -> None:
        """Deprecated. Override _process or _physics_process instead."""

    def _draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        """Override: called every frame for custom drawing."""

    # ── Internal frame dispatch ──────────────────────────────────────────────

    def _call_process(self, delta: float) -> None:
        """Called once per rendered frame. Traverses the tree and calls _process (or _update for backward compat)."""
        if not self.visible or self._queued_for_free:
            return
        if type(self)._process is not Node._process:
            self._process(delta)
        elif type(self)._update is not Node._update:
            self._update(delta)
        for child in self.children:
            child._call_process(delta)

    def _call_physics_process(self, delta: float) -> None:
        """Called at fixed timestep. Traverses the tree and calls _physics_process."""
        if not self.visible or self._queued_for_free:
            return
        if type(self)._physics_process is not Node._physics_process:
            self._physics_process(delta)
        for child in self.children:
            child._call_physics_process(delta)

    def _clear_canvas_items(self, canvas: tk.Canvas | None = None) -> None:
        target = canvas or getattr(self, '_canvas', None)
        if self._canvas_ids and target is not None:
            try:
                target.delete(*self._canvas_ids)
            except tk.TclError:
                # Canvas was destroyed or item IDs became invalid
                pass
            self._canvas_ids.clear()

    def _render(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        self._canvas = canvas
        if not self.visible or self._queued_for_free:
            self._clear_canvas_items(canvas)
            for child in self.children:
                child._render(canvas, cam)
            return
        # Try in-place update for retained rendering; fall back to clear+redraw
        if not self._update_draw(canvas, cam):
            self._clear_canvas_items(canvas)
            self._draw(canvas, cam)
        for child in self.children:
            child._render(canvas, cam)

    def _update_draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> bool:
        """Override to update existing canvas items in place.
        Return True if items were successfully updated without full redraw."""
        return False

    def _draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        """Override: called every frame for custom drawing."""
