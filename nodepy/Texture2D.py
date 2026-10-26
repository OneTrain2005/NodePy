from __future__ import annotations

import os
from typing import Optional, Tuple
from PIL import Image


class Texture2D:
    """
    Base texture class.  Wraps a PIL ``Image`` and assigns a unique integer ID
    used as part of the ``TextureManager`` cache key.

    Do not instantiate directly — use a subclass such as ``ImageTexture``.
    """

    _id_counter: int = 0

    def __init__(self, image: Image.Image) -> None:
        Texture2D._id_counter += 1
        self._id: int = Texture2D._id_counter
        self._image: Image.Image = image

    @property
    def texture_id(self) -> int:
        """Unique integer identifier for this texture instance."""
        return self._id

    @property
    def image(self) -> Image.Image:
        """The underlying PIL image (always RGBA)."""
        return self._image

    @property
    def width(self) -> int:
        return self._image.width

    @property
    def height(self) -> int:
        return self._image.height


class ImageTexture(Texture2D):
    """
    Texture loaded from an image file on disk.

    Uses a class-level cache keyed by absolute path so the same file is never
    read or decoded more than once per process.

    Usage
    -----
    tex = ImageTexture.load("assets/coin.png")
    """

    _cache: dict = {}

    def __init__(self, abs_path: str,
                 native_size: Optional[Tuple[int, int]] = None,
                 filter_mode: int = Image.BILINEAR) -> None:
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Texture not found: {abs_path!r}")
        image = Image.open(abs_path).convert("RGBA")
        if native_size is not None:
            image = image.resize(native_size, filter_mode)
        super().__init__(image)
        self._path = abs_path

    @classmethod
    def load(cls, path: str,
             native_size: Optional[Tuple[int, int]] = None,
             filter_mode: int = Image.BILINEAR) -> "ImageTexture":
        """
        Load and cache a texture by file path.

        Parameters
        ----------
        path:
            Relative or absolute path to the image file.  Paths are resolved
            to their absolute form before caching so relative paths from
            different working directories do not create duplicates.
        native_size:
            If given, the image is immediately downscaled to ``(w, h)`` after
            loading and the full-resolution source is discarded.  Use this when
            a texture will always be displayed at one fixed size — e.g. a
            256×256 PNG used as a 24×24 sprite.  The resized image is stored
            directly in ``texture.image`` so ``TextureManager._get_resized``
            returns it instantly with no PIL work and no extra copy in memory.
        filter_mode:
            PIL resampling filter used for the ``native_size`` downscale.
            Ignored when ``native_size`` is ``None``.
        """
        cache_key = (os.path.abspath(path), native_size)
        if cache_key not in cls._cache:
            cls._cache[cache_key] = cls(os.path.abspath(path), native_size, filter_mode)
        return cls._cache[cache_key]

    @property
    def path(self) -> str:
        """Absolute path to the source file."""
        return self._path
