from Engine.Node import Node
from Engine.Sprite2D import Sprite2D
from Engine.CollisionShape import CollisionShape
from Engine.Vector2d import Vector2d
from constants import SHIELD
class Shield(Node):
    def __init__(self, pos):
        super().__init__("Shield")
        self.relative_pos = pos
        self.hp = 3
        self.dead = False
        Sprite2D("s", texture=SHIELD, width=88, height=64, filter_mode=0, parent=self)
        self.col = CollisionShape("c", width=88, height=64, parent=self)
    def take_damage(self):
        if self.dead: return
        self.hp -= 1
        if self.hp <= 0:
            self.dead = True
            self.queue_free()
        else:
            self.scale = Vector2d(self.hp / 3, self.hp / 3)
