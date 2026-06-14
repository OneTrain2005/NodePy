from Engine.Node import Node
from Engine.ColorRect2D import ColorRect2D
from Engine.CollisionShape import CollisionShape
from Engine.Vector2d import Vector2d
from Engine.Signal import Signal
class Bullet(Node):
    SPEED = 380
    def __init__(self, pos, direction, owner):
        super().__init__("Bullet")
        self.relative_pos = pos
        self.dir = direction
        self.owner = owner
        self.dead = False
        self.is_enemy = owner == "enemy"
        self.is_player = owner == "player"
        ColorRect2D("v", width=4, height=12, color="#ffff00" if owner == "player" else "#ff4444", parent=self)
        self.col = CollisionShape("c", width=4, height=12, parent=self)
        self.col.body_entered += self._on_hit
        self.hit = Signal("hit")
    def _physics_process(self, dt):
        self.relative_pos += Vector2d(0, self.dir * self.SPEED * dt)
        if abs(self.relative_pos.y) > 400: self.queue_free()
    def _on_hit(self, other):
        target = other.parent
        if not target or getattr(target, "dead", False): return
        if self.owner == "enemy" and getattr(target, "is_enemy", False): return
        if self.owner == "player" and getattr(target, "is_player", False): return
        if isinstance(target, Bullet): return
        self.hit.emit(target)
        self.dead = True
        self.queue_free()
