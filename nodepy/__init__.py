"""NodePy — a Godot-inspired 2D game engine built in Python and tkinter.

Everything exported here is the public API that games and plugins can rely
on.  Names starting with an underscore may change between minor versions.
"""

__version__ = "1.1.0"

from nodepy.Vector2d import Vector2d
from nodepy.Matrix3x3 import Matrix3x3
from nodepy.Signal import Signal
from nodepy.Input import Input
from nodepy.Node import Node
from nodepy.Camera2D import Camera2D
from nodepy.Quadtree import SpatialHash
from nodepy.CollisionShape import CollisionShape
from nodepy.ColorRect2D import ColorRect2D
from nodepy.Texture2D import Texture2D, ImageTexture
from nodepy.TextureManager import TextureManager
from nodepy.Sprite2D import Sprite2D
from nodepy.Plugin import Plugin
from nodepy.GameLoop import GameLoop

__all__ = [
    "Vector2d", "Matrix3x3", "Signal", "Input", "Node", "Camera2D",
    "SpatialHash", "CollisionShape", "ColorRect2D", "Texture2D",
    "ImageTexture", "TextureManager", "Sprite2D", "Plugin", "GameLoop",
]
