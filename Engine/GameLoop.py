from __future__ import annotations
from Engine.Input import Input
from Engine.Matrix3x3 import Matrix3x3
from Engine.Node import Node
from Engine.Camera2D import Camera2D
from Engine.Quadtree import Quadtree
from Engine.CollisionShape import CollisionShape
from typing import Optional, List
import time
import tkinter as tk
import tkinter.ttk as ttk


class GameLoop:
    """
    Owns the tkinter root + canvas, wires up Input, drives the scene tree.

    The canvas is wrapped in a ``ttk.Frame`` and automatically expands to
    fill the window, so the game adapts to any size the user (or window
    manager) gives it.

    Usage
    -----
    loop = GameLoop(width=800, height=600, title="My Game")
    loop.set_scene(my_root_node)
    loop.run()
    """

    def __init__(self, width: int = 800, height: int = 600,
                 title: str = "PyEngine", bg: str = "#1a1a2e",
                 target_fps: int = 60, physics_fps: int = 60):
        self._requested_width = width
        self._requested_height = height
        self.target_fps = target_fps
        self._frame_ms = 1000 // target_fps

        self._physics_delta = 1.0 / physics_fps
        self._physics_accumulator = 0.0

        self.root = tk.Tk()
        self.root.title(title)
        self.root.minsize(200, 150)

        # ttk layout: frame fills the root window
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        # Canvas fills the frame and resizes with it
        self.canvas = tk.Canvas(self.frame, width=width, height=height,
                                bg=bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.width = width
        self.height = height

        # Wire Input to tkinter events
        self.root.bind("<KeyPress>", Input._on_key_press)
        self.root.bind("<KeyRelease>", Input._on_key_release)
        self.canvas.bind("<Motion>", Input._on_mouse_move)
        self.canvas.bind("<ButtonPress>", Input._on_mouse_press)
        self.canvas.bind("<ButtonRelease>", Input._on_mouse_release)

        # Track canvas resizing so the camera viewport stays in sync
        self.canvas.bind("<Configure>", self._on_resize)

        self._scene: Optional[Node] = None
        self._last_time = time.perf_counter()

        # FPS display
        self._fps_samples: List[float] = []
        self._fps_label_id: Optional[int] = None

    def _on_resize(self, event: tk.Event) -> None:
        """Update internal size and the active camera when the canvas changes."""
        new_w = event.width
        new_h = event.height
        if new_w == self.width and new_h == self.height:
            return
        self.width = new_w
        self.height = new_h

        cam = Camera2D._active
        if cam is not None:
            cam.viewport_w = new_w
            cam.viewport_h = new_h

    def set_scene(self, root_node: Node) -> None:
        self._scene = root_node
        root_node._call_ready()

    def _get_view_matrix(self) -> Matrix3x3:
        """Return the active camera's view matrix, or identity centred on origin."""
        cam = Camera2D._active
        if cam is not None:
            return cam.get_view_matrix()
        # Default: identity (world origin = top-left corner)
        return Matrix3x3()

    def _physics_step(self, delta: float) -> None:
        """Rebuild quadtree with fresh positions and run collision detection."""
        # Rebuild quadtree from all active collision shapes
        qt = Quadtree(bounds=(-4000, -4000, 4000, 4000))
        for shape in CollisionShape._all:
            if shape.visible and not shape._queued_for_free:
                qt.insert(shape)
        CollisionShape._quadtree = qt

        # Check collisions
        for shape in CollisionShape._all:
            if not shape.visible or shape._queued_for_free:
                continue
            if not shape.body_entered._listeners and not shape.body_exited._listeners:
                continue
            shape._check_collisions()

    def _tick(self) -> None:
        now = time.perf_counter()
        delta = now - self._last_time
        self._last_time = now

        # Fixed-timestep physics + collision
        self._physics_accumulator += delta
        while self._physics_accumulator >= self._physics_delta:
            if self._scene:
                self._scene._call_physics_process(self._physics_delta)
            self._physics_step(self._physics_delta)
            self._physics_accumulator -= self._physics_delta

        # Frame update (visual, variable delta)
        if self._scene:
            self._scene._call_process(delta)

        # Process deferred calls
        Node._flush_deferred_calls()

        # Process deferred frees
        if Node._deferred_free_queue:
            batch = list(Node._deferred_free_queue)
            Node._deferred_free_queue.clear()
            for node in batch:
                node._perform_free()

        # Input: flush per-frame state after all processing has seen it
        Input._flush()

        # Render
        self.canvas.delete("all")
        view = self._get_view_matrix()
        if self._scene:
            self._scene._render(self.canvas, view)

        # FPS overlay — anchored to the top-right of the current canvas size
        if delta > 0:
            self._fps_samples.append(1.0 / delta)
            if len(self._fps_samples) > 30:
                self._fps_samples.pop(0)
        avg_fps = sum(self._fps_samples) / max(1, len(self._fps_samples))
        self.canvas.create_text(
            self.width - 6, 6,
            text=f"{avg_fps:.0f} fps",
            anchor="ne", fill="#888888",
            font=("Helvetica", 9),
        )

        # Schedule next frame
        elapsed_ms = int((time.perf_counter() - now) * 1000)
        delay = max(1, self._frame_ms - elapsed_ms)
        self.root.after(delay, self._tick)

    def run(self) -> None:
        self.root.after(0, self._tick)
        self.root.mainloop()
