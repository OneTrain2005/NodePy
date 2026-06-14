from __future__ import annotations

import tkinter as tk
from collections import OrderedDict
from typing import TYPE_CHECKING, Tuple

from PIL import Image, ImageTk

if TYPE_CHECKING:
    from Engine.Texture2D import Texture2D

# (texture_id, quantised_rot_step, w_px, h_px, filter_mode)
_CacheKey    = Tuple[int, int, int, int, int]
# (texture_id, w_px, h_px, filter_mode)
_ResizeKey   = Tuple[int, int, int, int]


class TextureManager:
    """
    Global LRU cache: (texture_id, quantised_rotation, w_px, h_px) → PhotoImage.

    Design notes
    ------------
    **PhotoImage lifetime** — tkinter's canvas holds only a Tcl-level reference
    to each image.  If the Python ``PhotoImage`` object is garbage-collected the
    canvas silently goes blank.  This cache is the *sole* long-lived holder of
    every ``PhotoImage`` it creates; entries are only discarded via LRU eviction,
    never by GC.

    **Two-level caching** — a secondary unbounded dict caches the *resized* PIL
    image (source → target pixel size) separately from the rotated PhotoImages.
    The expensive downscale (e.g. 256×256 → 24×24 with BILINEAR) therefore
    happens exactly once per display size, regardless of how many rotation frames
    are baked from it.  PIL images are plain Python objects and are managed by
    the GC normally — no tkinter lifetime issue.

    **Rotation quantisation** — angles are snapped to the nearest ``rot_step``
    degrees (default 5°) before lookup.  This gives 72 unique frames per full
    revolution and dramatically increases cache hits for objects spinning at
    different speeds or with floating-point drift.

    **Scale encoding** — the caller computes the final pixel dimensions
    (texture natural size × matrix scale × zoom) and passes them as ``w_px`` /
    ``h_px``.  Integer pixel rounding acts as implicit scale quantisation.

    Usage
    -----
    photo = TextureManager.instance().get(texture, rot_deg, w_px, h_px)
    canvas.create_image(sx, sy, image=photo, anchor="center")
    """

    _instance: "TextureManager | None" = None

    def __init__(self, max_size: int = 512, rot_step: float = 5.0) -> None:
        """
        Parameters
        ----------
        max_size:
            Maximum number of ``PhotoImage`` entries in the LRU cache.  When
            exceeded the least-recently-used entry is evicted.
        rot_step:
            Rotation quantisation granularity in degrees.  Must divide evenly
            into 360 (e.g. 1, 2, 3, 4, 5, 6, 9, 10, 12, 15, 18, 30, 45, 90).
        """
        self._cache: OrderedDict[_CacheKey, tk.PhotoImage] = OrderedDict()
        # Unbounded: one entry per (texture, w, h, filter) — PIL objects, GC-managed
        self._resized: OrderedDict[_ResizeKey, Image.Image] = OrderedDict()
        self.max_size = max_size
        self.rot_step = rot_step
        self._steps: int = round(360.0 / rot_step)

    @classmethod
    def instance(cls) -> "TextureManager":
        """Return (or create) the singleton TextureManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Public API ───────────────────────────────────────────────────────────

    def get(self, texture: "Texture2D",
            rot_deg: float, w_px: int, h_px: int,
            filter_mode: int = Image.BILINEAR) -> tk.PhotoImage:
        """
        Return a ``PhotoImage`` for the given texture, rotation, and pixel size.

        Parameters
        ----------
        texture:
            Source texture.  Its ``texture_id`` is part of the cache key.
        rot_deg:
            Clockwise rotation in degrees (matches the engine's screen-space
            convention).  Quantised to the nearest ``rot_step`` degrees.
        w_px, h_px:
            Final output pixel dimensions (texture size × scale × zoom,
            pre-computed by the caller from the decomposed matrix).
        filter_mode:
            PIL resampling filter used for the resize step.  Common values::

                Image.NEAREST  — fastest, pixelated
                Image.BOX      — fast, good for heavy downscaling
                Image.BILINEAR — default, smooth (Image.LINEAR is the same)
                Image.BICUBIC  — higher quality, slower
                Image.LANCZOS  — best quality, slowest

            Note: ``Image.LINEAR`` is a PIL alias for ``Image.BILINEAR`` —
            they are identical in every way.
        """
        w_px = max(1, w_px)
        h_px = max(1, h_px)
        q_rot = int(round(rot_deg / self.rot_step)) % self._steps
        key: _CacheKey = (texture.texture_id, q_rot, w_px, h_px, filter_mode)

        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        photo = self._bake(texture, q_rot * self.rot_step, w_px, h_px, filter_mode)
        self._cache[key] = photo
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)   # evict LRU
        return photo

    def prewarm(self, texture: "Texture2D", w_px: int, h_px: int,
                filter_mode: int = Image.BILINEAR) -> None:
        """
        Pre-bake every rotation frame for a texture at the given display size.

        Call this during scene setup (before ``loop.run()``) to push all PIL
        work into load time rather than spreading it across the first few seconds
        of gameplay.  With 72 frames at the default 5° step, each call bakes
        one resize + 72 BICUBIC rotations up front.

        Parameters
        ----------
        texture:
            The texture to pre-bake.
        w_px, h_px:
            Display pixel dimensions — pass the same values Sprite2D will
            compute (typically ``round(sprite.width * zoom)``).
        filter_mode:
            PIL resampling filter for the resize step.  Must match the value
            passed to ``Sprite2D`` so cache keys align.
        """
        w_px = max(1, w_px)
        h_px = max(1, h_px)
        for step in range(self._steps):
            key: _CacheKey = (texture.texture_id, step, w_px, h_px, filter_mode)
            if key not in self._cache:
                self._cache[key] = self._bake(
                    texture, step * self.rot_step, w_px, h_px, filter_mode
                )
        # Trim to max_size if prewarm pushed us over (keep newest entries)
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Drop all cached frames and resized intermediates."""
        self._cache.clear()
        self._resized.clear()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _get_resized(self, texture: "Texture2D",
                     w_px: int, h_px: int,
                     filter_mode: int = Image.BILINEAR) -> Image.Image:
        """
        Return the source image downscaled to ``(w_px, h_px)``, from cache.

        The resize is computed once per (texture, size, filter_mode) triple.
        Cheaper filters (NEAREST, BOX) are significantly faster for large
        source images being heavily downscaled with no perceptible quality
        loss at typical sprite display sizes.
        """
        rkey: _ResizeKey = (texture.texture_id, w_px, h_px, filter_mode)
        if rkey in self._resized:
            self._resized.move_to_end(rkey)
            return self._resized[rkey]

        img = texture.image
        # Skip PIL resize when source is already the right size — this is
        # the common case when ImageTexture was loaded with native_size.
        if img.width == w_px and img.height == h_px:
            self._resized[rkey] = img
        else:
            self._resized[rkey] = img.resize((w_px, h_px), filter_mode)

        # Cap resized cache to prevent unbounded growth
        while len(self._resized) > self.max_size * 2:
            self._resized.popitem(last=False)

        return self._resized[rkey]

    def _bake(self, texture: "Texture2D",
              rot_deg: float, w_px: int, h_px: int,
              filter_mode: int = Image.BILINEAR) -> tk.PhotoImage:
        """
        Rotate the already-resized image and convert to a ``PhotoImage``.

        The resize step is served from ``_resized`` cache — for a 256×256
        source at a 24×24 display size this means the expensive downscale
        runs once regardless of how many rotation frames are baked.

        ``expand=True`` ensures the output canvas grows to contain the full
        rotated image so corners are never clipped.  ``BICUBIC`` resampling
        on the small rotated image keeps edges clean at negligible cost.
        """
        out = self._get_resized(texture, w_px, h_px, filter_mode)
        if rot_deg % 360.0 != 0.0:
            # PIL rotates counter-clockwise; negate to match the engine's
            # clockwise-positive convention.
            out = out.rotate(-rot_deg, expand=True, resample=Image.BILINEAR)
        return ImageTk.PhotoImage(out)
