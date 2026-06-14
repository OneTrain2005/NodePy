"""Unit tests for Engine.TextureManager"""

import pytest
from PIL import Image
import tkinter as tk

from Engine.TextureManager import TextureManager
from Engine.Texture2D import Texture2D


# TextureManager._bake creates ImageTk.PhotoImage which needs a tkinter root.
# We create a hidden one at module import time for the whole test file.
_tk_root = None


def _ensure_tk_root():
    global _tk_root
    if _tk_root is None:
        _tk_root = tk.Tk()
        _tk_root.withdraw()
    return _tk_root


@pytest.fixture(scope="module", autouse=True)
def tk_root_fixture():
    root = _ensure_tk_root()
    yield root


@pytest.fixture
def tm():
    """Provide a fresh TextureManager instance."""
    old = TextureManager._instance
    TextureManager._instance = None
    instance = TextureManager.instance()
    yield instance
    instance.clear()
    TextureManager._instance = old


@pytest.fixture
def dummy_texture():
    """Provide a simple texture for testing."""
    img = Image.new("RGBA", (16, 16), color=(255, 0, 0, 255))
    return Texture2D(img)


class TestTextureManagerSingleton:
    def test_instance_creates_singleton(self, tm):
        assert TextureManager._instance is tm

    def test_instance_returns_same(self, tm):
        assert TextureManager.instance() is tm


class TestTextureManagerGet:
    def test_get_caches_result(self, tm, dummy_texture):
        photo1 = tm.get(dummy_texture, 0, 8, 8)
        photo2 = tm.get(dummy_texture, 0, 8, 8)
        assert photo1 is photo2

    def test_get_different_rotations_different_cache(self, tm, dummy_texture):
        photo1 = tm.get(dummy_texture, 0, 8, 8)
        photo2 = tm.get(dummy_texture, 5, 8, 8)
        assert photo1 is not photo2

    def test_get_quantises_rotation(self, tm, dummy_texture):
        # 1° and 2° both quantise to 0 with default 5° step
        photo1 = tm.get(dummy_texture, 1, 8, 8)
        photo2 = tm.get(dummy_texture, 2, 8, 8)
        assert photo1 is photo2

    def test_get_clamps_dimensions_to_one(self, tm, dummy_texture):
        photo = tm.get(dummy_texture, 0, 0, 0)
        # Should not raise; internally clamped to 1
        assert photo is not None

    def test_get_moves_to_end_on_hit(self, tm, dummy_texture):
        tm.max_size = 2
        t2 = Texture2D(Image.new("RGBA", (8, 8)))
        tm.get(dummy_texture, 0, 4, 4)
        tm.get(t2, 0, 4, 4)
        # Access first entry again
        tm.get(dummy_texture, 0, 4, 4)
        # Add a third to force eviction
        t3 = Texture2D(Image.new("RGBA", (4, 4)))
        tm.get(t3, 0, 2, 2)
        # t2 (LRU) should have been evicted
        assert (t2.texture_id, 0, 4, 4, Image.BILINEAR) not in tm._cache


class TestTextureManagerPrewarm:
    def test_prewarm_populates_cache(self, tm, dummy_texture):
        tm.prewarm(dummy_texture, 8, 8)
        steps = tm._steps  # default 360/5 = 72
        assert len(tm._cache) == steps

    def test_prewarm_does_not_duplicate(self, tm, dummy_texture):
        tm.prewarm(dummy_texture, 8, 8)
        count_before = len(tm._cache)
        tm.prewarm(dummy_texture, 8, 8)
        assert len(tm._cache) == count_before

    def test_prewarm_respects_max_size(self, tm, dummy_texture):
        tm.max_size = 10
        tm.prewarm(dummy_texture, 8, 8)
        assert len(tm._cache) <= tm.max_size


class TestTextureManagerClear:
    def test_clear_empties_cache(self, tm, dummy_texture):
        tm.get(dummy_texture, 0, 8, 8)
        tm.clear()
        assert len(tm._cache) == 0
        assert len(tm._resized) == 0


class TestTextureManagerResizedCache:
    def test_resized_cached(self, tm, dummy_texture):
        img1 = tm._get_resized(dummy_texture, 8, 8)
        img2 = tm._get_resized(dummy_texture, 8, 8)
        assert img1 is img2

    def test_resized_same_size_returns_original(self, tm, dummy_texture):
        # dummy_texture is 16x16; ask for 16x16
        img = tm._get_resized(dummy_texture, 16, 16)
        assert img is dummy_texture.image

    def test_resized_different_sizes(self, tm, dummy_texture):
        img1 = tm._get_resized(dummy_texture, 8, 8)
        img2 = tm._get_resized(dummy_texture, 4, 4)
        assert img1 is not img2
        assert img1.size == (8, 8)
        assert img2.size == (4, 4)
