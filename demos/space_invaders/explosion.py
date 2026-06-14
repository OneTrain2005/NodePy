from Engine.Node import Node
from Engine.Sprite2D import Sprite2D
from constants import BOOM
class Explosion(Node):
    LIFE = 0.25
    def __init__(self, pos):
        super().__init__("Explosion")
        self.relative_pos = pos
        Sprite2D("s", texture=BOOM, width=52, height=32, filter_mode=0, parent=self)
        self._t = self.LIFE
    def _process(self, dt):
        self._t -= dt
        if self._t <= 0: self.queue_free()
