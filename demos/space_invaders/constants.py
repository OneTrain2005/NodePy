import sys
from pathlib import Path
from PIL import Image
from Engine.Texture2D import ImageTexture
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
ASSETS = Path(__file__).resolve().parent / "assets"
def load(n, s): return ImageTexture.load(ASSETS / n, native_size=s, filter_mode=Image.NEAREST)
PLAYER = load("player.webp", (52, 32))
SMALL = load("small_enemy.webp", (32, 32))
MED = load("medium_enemy.webp", (44, 32))
BIG = load("big_enemy.webp", (48, 32))
MOTH = load("mothership.webp", (96, 42))
SHIELD = load("shield.webp", (88, 64))
BOOM = load("explosion.webp", (52, 32))
