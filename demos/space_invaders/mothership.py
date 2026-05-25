import random
from Engine.Node import Node
from Engine.Sprite2D import Sprite2D
from Engine.CollisionShape import CollisionShape
from Engine.Vector2d import Vector2d
from Engine.Signal import Signal
from constants import MOTH
class Mothership(Node):
    def __init__(self):
        super().__init__("Mothership")
        self.dead = False
        self.is_enemy = True
        self.dir = random.choice([-1, 1])
        self.relative_pos = Vector2d(-460 if self.dir == 1 else 460, -260)
        Sprite2D("s", texture=MOTH, width=96, height=42, filter_mode=0, parent=self)
        self.col = CollisionShape("c", width=96, height=42, parent=self)
        self.died = Signal("died")
    def _update(self, dt):
        self.relative_pos += Vector2d(self.dir * 100 * dt, 0)
        if abs(self.relative_pos.x) > 520: self.queue_free()
    def die(self):
        if self.dead: return
        self.dead = True
        self.died.emit(self)
        self.queue_free()
