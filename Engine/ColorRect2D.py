from __future__ import annotations

from typing import Optional

import tkinter as tk

from Engine.Camera2D import Camera2D
from Engine.Matrix3x3 import Matrix3x3
from Engine.Node import Node


class ColorRect2D(Node):
    """
    Draws a solid-colour rectangle in world space using ``canvas.create_polygon``.

    This is the rename of the original ``Sprite2D`` after the node split.  Use
    this for geometry that has no texture — player debug shapes, UI elements,
    placeholder art, etc.  For image-based rendering use ``Sprite2D`` instead.

    Parameters
    ----------
    name    Node name.
    width   Local-space width  (centred on origin).
    height  Local-space height (centred on origin).
    color   tkinter fill colour string (``"red"``, ``"#ff0000"``, …).
    outline Outline colour.  Pass ``""`` for no outline.
    label   Optional text rendered at the node origin in screen space.
    """

    def __init__(self, name: str, width: float = 20, height: float = 20,
                 color: str = "white", outline: str = "white",
                 label: str = "", parent: Optional[Node] = None) -> None:
        super().__init__(name, parent=parent)
        self.width   = width
        self.height  = height
        self.color   = color
        self.outline = outline
        self.label   = label

    def _compute_pts(self, cam: Matrix3x3) -> list[float]:
        mat = cam * self.global_matrix
        hw, hh = self.width / 2, self.height / 2
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        pts = []
        for px, py in corners:
            sx, sy = mat.multiply_vec(px, py)
            pts.extend([sx, sy])
        return pts

    def _update_draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> bool:
        if len(self._canvas_ids) != (2 if self.label else 1):
            return False
        pts = self._compute_pts(cam)
        # Update polygon coords in place
        canvas.coords(self._canvas_ids[0], *pts)
        if self.label:
            ox, oy = (cam * self.global_matrix).multiply_vec(0, 0)
            canvas.coords(self._canvas_ids[1], ox, oy)
        return True

    def _draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        active = Camera2D._active
        if active is not None:
            vw, vh = active.viewport_w, active.viewport_h
            ref = self.parent if self.parent is not None else self
            wx, wy = ref.global_matrix.multiply_vec(
                self._relative_pos.x, self._relative_pos.y
            )
            sx, sy = cam.multiply_vec(wx, wy)
            margin = (self.width + self.height) * active.zoom
            if sx + margin < 0 or sx - margin > vw or \
               sy + margin < 0 or sy - margin > vh:
                return

        pts = self._compute_pts(cam)

        # Exact cull
        if active is not None:
            if (pts[0] < 0 and pts[2] < 0 and pts[4] < 0 and pts[6] < 0) or \
               (pts[0] > vw and pts[2] > vw and pts[4] > vw and pts[6] > vw) or \
               (pts[1] < 0 and pts[3] < 0 and pts[5] < 0 and pts[7] < 0) or \
               (pts[1] > vh and pts[3] > vh and pts[5] > vh and pts[7] > vh):
                return

        self._canvas_ids.append(
            canvas.create_polygon(pts, fill=self.color,
                                  outline=self.outline, width=1)
        )
        if self.label:
            ox, oy = (cam * self.global_matrix).multiply_vec(0, 0)
            self._canvas_ids.append(
                canvas.create_text(ox, oy, text=self.label,
                                   fill="white", font=("Helvetica", 8))
            )
