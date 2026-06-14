"""Unit tests for Engine.Texture2D"""

import os
import pytest
from PIL import Image
from Engine.Texture2D import Texture2D, ImageTexture


class TestTexture2DBase:
    def test_id_counter_increments(self):
        before = Texture2D._id_counter
        img = Image.new("RGBA", (10, 10))
        tex = Texture2D(img)
        assert tex.texture_id == before + 1

    def test_width_height(self):
        img = Image.new("RGBA", (32, 64))
        tex = Texture2D(img)
        assert tex.width == 32
        assert tex.height == 64

    def test_image_property(self):
        img = Image.new("RGBA", (10, 10))
        tex = Texture2D(img)
        assert tex.image is img


class TestImageTexture:
    def test_load_existing_file(self):
        tex = ImageTexture.load("demos/coin_collector/coin.png")
        assert tex.width > 0
        assert tex.height > 0
        assert os.path.isabs(tex.path)

    def test_load_caches_same_path(self):
        tex1 = ImageTexture.load("demos/coin_collector/coin.png")
        tex2 = ImageTexture.load("demos/coin_collector/coin.png")
        assert tex1 is tex2

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            ImageTexture.load("demos/nonexistent.png")

    def test_load_with_native_size(self):
        tex = ImageTexture.load("demos/coin_collector/coin.png", native_size=(16, 16))
        assert tex.width == 16
        assert tex.height == 16

    def test_load_different_sizes_not_same_cache(self):
        tex1 = ImageTexture.load("demos/coin_collector/coin.png")
        tex2 = ImageTexture.load("demos/coin_collector/coin.png", native_size=(16, 16))
        assert tex1 is not tex2

    def test_path_is_absolute(self):
        tex = ImageTexture.load("demos/coin_collector/coin.png")
        assert tex.path.startswith("/")


@pytest.fixture(autouse=True)
def clear_image_texture_cache():
    """Clear ImageTexture cache before and after tests."""
    original_cache = dict(ImageTexture._cache)
    ImageTexture._cache.clear()
    yield
    ImageTexture._cache.clear()
    ImageTexture._cache.update(original_cache)
