"""
Demo scene for pyengine.

What's happening
----------------
Player  A yellow square the user controls with WASD / arrow keys.
        Carries a CollisionShape; emits a signal when it bumps a Coin.
Coin    Spinning orange diamonds scattered around the world.
        When the player overlaps one it disappears and the score goes up.
Camera  Follows the player smoothly with a slight lag.
HUD     Screen-space label showing score and controls.
        It is a child of a plain Node positioned in screen space so it
        ignores the camera transform.
"""

from Engine.Node import Node
from Engine.Sprite2D import Sprite2D
from Engine.CollisionShape import CollisionShape
from Engine.GameLoop import GameLoop
from Engine.Input import Input
from Engine.Matrix3x3 import Matrix3x3
from Engine.Signal import Signal
from Engine.Vector2d import Vector2d
from Engine.Camera2D import Camera2D
import random

# ─────────────────────────────────────────────────────────────────────────────
# Player
# ─────────────────────────────────────────────────────────────────────────────

class Player(Node):
    SPEED = 180.0   # px / second

    def __init__(self):
        super().__init__("Player")
        self.score = 0

        # Visual
        self.sprite = Sprite2D("sprite", width=28, height=28,
                               color="#f6c90e", outline="#ffd700",
                               parent=self)

        # Collision
        self.col = CollisionShape("col", width=28, height=28,
                                  debug_draw=True, parent=self)
        self.col.body_entered.connect(self._on_body_entered)

        # Custom signal: score changed
        self.score_changed = Signal("score_changed")

    def _ready(self) -> None:
        self.relative_pos = Vector2d(0, 0)

    def _update(self, delta: float) -> None:
        direction = Input.get_vector("move_left", "move_right",
                                     "move_up",    "move_down")
        if direction.length() > 0:
            direction = direction.normalized()
        self.relative_pos = self.relative_pos + direction * (self.SPEED * delta)

        # Rotate sprite slightly based on horizontal movement for juice
        self.sprite.rotation = self.sprite.rotation + direction.x * 90 * delta

    def _on_body_entered(self, other: CollisionShape) -> None:
        # Check if we hit a Coin's collision shape
        if other.parent is not None and isinstance(other.parent, Coin):
            coin: Coin = other.parent
            if coin.visible:
                coin.collect()
                self.score += 1
                self.score_changed.emit(self.score)


# ─────────────────────────────────────────────────────────────────────────────
# Coin
# ─────────────────────────────────────────────────────────────────────────────

class Coin(Node):
    def __init__(self, pos: Vector2d):
        super().__init__("Coin")
        self.relative_pos = pos
        self._spin = 0.0

        self.sprite = Sprite2D("sprite", width=16, height=16,
                               color="#ff8c00", outline="#ffa500",
                               parent=self)
        self.sprite.rotation = 45   # diamond shape

        self.col = CollisionShape("col", width=16, height=16,
                                  debug_draw=False, parent=self)

    def _update(self, delta: float) -> None:
        self._spin += 120 * delta
        self.sprite.rotation = 45 + self._spin

    def collect(self) -> None:
        self.visible = False


# ─────────────────────────────────────────────────────────────────────────────
# HUD  (lives in screen space — NOT a child of any world node)
# ─────────────────────────────────────────────────────────────────────────────

class HUD(Node):
    """
    Drawn last, in screen space.  We override _draw directly and skip the
    camera matrix by multiplying by identity instead of `cam`.
    """

    def __init__(self):
        super().__init__("HUD")
        self._score = 0

    def set_score(self, score: int) -> None:
        self._score = score

    def _draw(self, canvas, cam) -> None:
        import tkinter as tk
        # Ignore camera — draw directly in screen coords
        canvas.create_text(
            14, 14, anchor="nw",
            text=f"Coins: {self._score}",
            fill="white", font=("Helvetica", 14, "bold"),
        )
        canvas.create_text(
            14, 36, anchor="nw",
            text="WASD / arrows to move",
            fill="#aaaaaa", font=("Helvetica", 10),
        )


# ─────────────────────────────────────────────────────────────────────────────
# SmoothCamera  (follows a target with lerp)
# ─────────────────────────────────────────────────────────────────────────────

class SmoothCamera(Camera2D):
    LERP_SPEED = 5.0   # higher = snappier follow

    def __init__(self, target: Node, viewport_size):
        super().__init__("Camera2D", viewport_size=viewport_size, zoom=1.0)
        self.target = target

    def _update(self, delta: float) -> None:
        tp = self.target.global_position
        cp = self.global_position
        # Exponential lerp
        nx = cp.x + (tp.x - cp.x) * min(1.0, self.LERP_SPEED * delta)
        ny = cp.y + (tp.y - cp.y) * min(1.0, self.LERP_SPEED * delta)
        self.relative_pos = Vector2d(nx, ny)


# ─────────────────────────────────────────────────────────────────────────────
# Scene assembly
# ─────────────────────────────────────────────────────────────────────────────

def build_scene(loop: GameLoop) -> Node:
    VP = (loop.width, loop.height)

    # Root node — everything lives under here
    root = Node("Root")

    # ── World ────────────────────────────────────────────────────────────────

    world = Node("World")
    root.add_child(world)

    # Background grid (visual reference only — a grid of small dots)
    bg = _GridBackground("BG", spacing=60,
                          width=loop.width, height=loop.height)
    world.add_child(bg)
    #debug_overlay = DebugOverlay()
    #world.add_child(debug_overlay)
    # Player
    player = Player()
    world.add_child(player)

    for _ in range(1000):
        pos = Vector2d(random.uniform(-3000, 3000), random.uniform(-3000, 3000))
        world.add_child(Coin(pos))

    # ── Camera ───────────────────────────────────────────────────────────────

    camera = SmoothCamera(target=player, viewport_size=VP)
    world.add_child(camera)
    camera.make_active()

    # ── HUD (screen space — child of root, not world) ─────────────────────

    hud = HUD()
    root.add_child(hud)

    # Connect player score signal → HUD
    player.score_changed.connect(hud.set_score)

    return root


# ─────────────────────────────────────────────────────────────────────────────
# GridBackground helper
# ─────────────────────────────────────────────────────────────────────────────

class _GridBackground(Node):
    """Draws a subtle dot grid in world space for spatial reference."""

    def __init__(self, name: str, spacing: int, width: int, height: int):
        super().__init__(name)
        self.spacing = spacing
        self.half_w  = width  // 2 + spacing * 2
        self.half_h  = height // 2 + spacing * 2

    def _draw(self, canvas, cam: "Matrix3x3") -> None:
        s = self.spacing
        for wx in range(-self.half_w, self.half_w + 1, s):
            for wy in range(-self.half_h, self.half_h + 1, s):
                sx, sy = cam.multiply_vec(wx, wy)
                canvas.create_oval(sx - 1, sy - 1, sx + 1, sy + 1,
                                   fill="#2a2a4a", outline="")

# ─────────────────────────────────────────────────────────────────────────────
# QuadtreeDbugDraw -- child of world node
# ─────────────────────────────────────────────────────────────────────────────
class DebugOverlay(Node):
    def __init__(self):
        super().__init__("DebugOverlay")
        self.enabled = True

    def _update(self, delta):
        # Toggle with a key press
        if Input.is_action_just_pressed("F1"):
            self.enabled = not self.enabled

    def _draw(self, canvas, cam):
        if not self.enabled:
            return
        qt = CollisionShape._quadtree
        if qt is not None:
            qt.debug_draw(canvas, cam)

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loop = GameLoop(width=800, height=600,
                    title="PyEngine demo — collect the coins",
                    bg="#0f0f1e")
    scene = build_scene(loop)
    loop.set_scene(scene)
    loop.run()
