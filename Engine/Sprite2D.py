from __future__ import annotations

from typing import Optional

import tkinter as tk
from PIL import Image

from Engine.Camera2D import Camera2D
from Engine.Matrix3x3 import Matrix3x3
from Engine.Node import Node
from Engine.Texture2D import Texture2D
from Engine.TextureManager import TextureManager


class Sprite2D(Node):
    """
    Draws a ``Texture2D`` in world space using ``canvas.create_image``.

    The full transform (position, rotation, scale, camera zoom) is decomposed
    from the combined ``cam * global_matrix`` each frame.  Rotation and scale
    are baked into a ``PhotoImage`` by ``TextureManager`` (which caches and
    quantises them); only position is passed to tkinter's ``create_image`` call.

    Parameters
    ----------
    name          Node name.
    texture       The ``Texture2D`` to render.
    width         Display width in local space.  Defaults to ``texture.width``.
    height        Display height in local space.  Defaults to ``texture.height``.
    filter_mode   PIL resampling filter for the resize bake step.  Common values:
                  ``Image.NEAREST`` (fastest), ``Image.BOX``, ``Image.BILINEAR``
                  (default), ``Image.BICUBIC``, ``Image.LANCZOS`` (best quality).
                  Must match the value passed to ``TextureManager.prewarm`` so
                  cache keys align.
    parent        Optional parent node.

    Notes
    -----
    For solid-colour geometry without a texture use ``ColorRect2D`` instead.
    """

    def __init__(self, name: str, texture: Texture2D,
                 width: Optional[float] = None,
                 height: Optional[float] = None,
                 filter_mode: int = Image.BILINEAR,
                 parent: Optional[Node] = None) -> None:
        super().__init__(name, parent=parent)
        self.texture     = texture
        self.width       = float(width  if width  is not None else texture.width)
        self.height      = float(height if height is not None else texture.height)
        self.filter_mode = filter_mode

    def _draw(self, canvas: tk.Canvas, cam: Matrix3x3) -> None:
        active = Camera2D._active

        # ── Pre-cull (cheap) ─────────────────────────────────────────────────
        # Project the sprite centre via the parent's already-cached global
        # matrix.  This avoids recomputing the dirty local matrix for off-screen
        # sprites — the dominant cost before culling was introduced.
        if active is not None:
            vw, vh = active.viewport_w, active.viewport_h
            ref = self.parent if self.parent is not None else self
            wx, wy = ref.global_matrix.multiply_vec(
                self._relative_pos.x, self._relative_pos.y
            )
            sx, sy = cam.multiply_vec(wx, wy)
            # Margin covers the worst-case rotated bounding circle of the sprite.
            margin = (self.width + self.height) * active.zoom
            if sx + margin < 0 or sx - margin > vw or \
               sy + margin < 0 or sy - margin > vh:
                return

        # ── Full matrix + decompose ──────────────────────────────────────────
        mat = cam * self.global_matrix
        tx, ty, rot_deg, scale_x, scale_y = mat.decompose()

        # Pixel dimensions at the current scale / zoom.  Integer rounding acts
        # as implicit scale quantisation (no sub-pixel cache misses).
        w_px = max(1, round(self.width  * scale_x))
        h_px = max(1, round(self.height * scale_y))

        # ── Exact screen-rect cull ───────────────────────────────────────────
        # After expand=True rotation the baked image is at most
        # hypot(w,h) wide/tall.  We use (w+h)/2 as a conservative radius.
        if active is not None:
            r = (w_px + h_px) / 2
            if tx + r < 0 or tx - r > vw or ty + r < 0 or ty - r > vh:
                return

        # ── Fetch / bake from cache and draw ─────────────────────────────────
        photo = TextureManager.instance().get(
            self.texture, rot_deg, w_px, h_px, self.filter_mode
        )
        canvas.create_image(tx, ty, image=photo, anchor="center")
