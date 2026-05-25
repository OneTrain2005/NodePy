import random
from Engine.Node import Node
from Engine.Sprite2D import Sprite2D
from Engine.CollisionShape import CollisionShape
from Engine.Vector2d import Vector2d
from Engine.Signal import Signal
from constants import BIG, MED, SMALL
class Enemy(Node):
    def __init__(self, name, tex, w, h, score):
        super().__init__(name)
        self.score = score
        self.dead = False
        self.is_enemy = True
        Sprite2D("s", texture=tex, width=w, height=h, filter_mode=0, parent=self)
        self.col = CollisionShape("c", width=w, height=h, parent=self)
        self.died = Signal("died")
    def die(self):
        if self.dead: return
        self.dead = True
        self.died.emit(self)
        self.queue_free()
class EnemyFormation(Node):
    def __init__(self):
        super().__init__("EnemyFormation")
        self.direction = 1
        self.speed = 28
        self.drop = 18
        self.shoot_timer = 1.2
        self.shot = Signal("shot")
        self.enemy_died = Signal("enemy_died")
        self.reached_bottom = Signal("reached_bottom")
        rows = [(BIG, 48, 32, 10), (MED, 44, 32, 20), (SMALL, 32, 32, 30)]
        for ri, (tex, w, h, score) in enumerate(rows):
            for ci in range(8):
                e = Enemy(f"E{ri}_{ci}", tex, w, h, score)
                e.relative_pos = Vector2d(ci * 50 - 175, ri * 38 - 60)
                e.died += lambda enemy, e=e: self.enemy_died.emit(e)
                self.add_child(e)
    def _update(self, dt):
        self.relative_pos += Vector2d(self.direction * self.speed * dt, 0)
        if not self.children: return
        left = min(c.global_position.x for c in self.children)
        right = max(c.global_position.x for c in self.children)
        if right > 360 or left < -360:
            self.direction *= -1
            self.relative_pos += Vector2d(0, self.drop)
            self.speed = min(self.speed + 2, 90)
        bottom = max(c.global_position.y for c in self.children)
        if bottom > 220: self.reached_bottom.emit()
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = max(0.4, 1.6 - self.speed / 50)
            self._shoot()
    def _shoot(self):
        alive = [c for c in self.children if isinstance(c, Enemy) and not c.dead]
        if not alive: return
        s = random.choice(alive)
        self.shot.emit(s.global_position + Vector2d(0, 20))
