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
class GameLoop:
    """
    Owns the tkinter root + canvas, wires up Input, drives the scene tree.

    Usage
    -----
    loop = GameLoop(width=800, height=600, title="My Game")
    loop.set_scene(my_root_node)
    loop.run()
    """

    def __init__(self, width: int = 800, height: int = 600,
                 title: str = "PyEngine", bg: str = "#1a1a2e",
                 target_fps: int = 60):
        self.width  = width
        self.height = height
        self.target_fps = target_fps
        self._frame_ms  = 1000 // target_fps

        self.root   = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=width, height=height,
                                bg=bg, highlightthickness=0)
        self.canvas.pack()

        # Wire Input to tkinter events
        self.root.bind("<KeyPress>",         Input._on_key_press)
        self.root.bind("<KeyRelease>",       Input._on_key_release)
        self.canvas.bind("<Motion>",         Input._on_mouse_move)
        self.canvas.bind("<ButtonPress>",    Input._on_mouse_press)
        self.canvas.bind("<ButtonRelease>",  Input._on_mouse_release)

        self._scene: Optional[Node] = None
        self._last_time = time.perf_counter()

        # FPS display
        self._fps_samples: List[float] = []
        self._fps_label_id: Optional[int] = None

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

    def _tick(self) -> None:
        now   = time.perf_counter()
        delta = now - self._last_time
        self._last_time = now

        # ── Input: flush per-frame state before any _update sees it ──────────
        Input._flush()

        # ── Rebuild quadtree from all active collision shapes ─────────────────
        # Done once here so every CollisionShape._update() this frame shares
        # the same spatial index — O(n log n) instead of O(n²).
        qt = Quadtree(bounds=(-4000, -4000, 4000, 4000))
        for shape in CollisionShape._all:
            if shape.visible:
                qt.insert(shape)
        CollisionShape._quadtree = qt

        # ── Update scene tree ────────────────────────────────────────────────
        if self._scene:
            self._scene._process(delta)

        # ── Process deferred frees ───────────────────────────────────────────
        if Node._deferred_free_queue:
            batch = list(Node._deferred_free_queue)
            Node._deferred_free_queue.clear()
            for node in batch:
                node._perform_free()

        # ── Render ───────────────────────────────────────────────────────────
        self.canvas.delete("all")
        view = self._get_view_matrix()
        if self._scene:
            self._scene._render(self.canvas, view)

        # ── FPS overlay ──────────────────────────────────────────────────────
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

        # ── Schedule next frame ───────────────────────────────────────────────
        elapsed_ms = int((time.perf_counter() - now) * 1000)
        delay = max(1, self._frame_ms - elapsed_ms)
        self.root.after(delay, self._tick)

    def run(self) -> None:
        self.root.after(0, self._tick)
        self.root.mainloop()
