from nodepy.Node import Node
from nodepy.Sprite2D import Sprite2D
from nodepy.CollisionShape import CollisionShape
from nodepy.Input import Input
from nodepy.Vector2d import Vector2d
from nodepy.Signal import Signal
from constants import PLAYER
class Player(Node):
    SPEED = 260
    COOLDOWN = 0.35
    def __init__(self):
        super().__init__("Player")
        self.alive = True
        self.is_player = True
        self._cool = 0
        self.sprite = Sprite2D("s", texture=PLAYER, width=52, height=32, filter_mode=0, parent=self)
        self.col = CollisionShape("c", width=52, height=32, parent=self)
        self.died = Signal("died")
        self.shot = Signal("shot")
    def _ready(self):
        self.relative_pos = Vector2d(0, 250)
    def _physics_process(self, dt):
        if not self.alive: return
        self.relative_pos += Vector2d(Input.get_axis("move_left", "move_right") * self.SPEED * dt, 0)
        self.relative_pos = Vector2d(max(-370, min(370, self.relative_pos.x)), self.relative_pos.y)
        self._cool -= dt
        if Input.is_action_pressed("shoot") and self._cool <= 0:
            self.shot.emit(self.global_position + Vector2d(0, -20))
            self._cool = self.COOLDOWN
    def hit(self):
        if not self.alive: return
        self.alive = False
        self.sprite.visible = False
        self.col.visible = False
        self.died.emit(self.global_position)
