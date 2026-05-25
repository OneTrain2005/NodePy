import random
from Engine.Node import Node
from Engine.Input import Input
from Engine.Vector2d import Vector2d
from player import Player
from enemy import Enemy, EnemyFormation
from shield import Shield
from mothership import Mothership
from bullet import Bullet
from explosion import Explosion
class GameManager(Node):
    def __init__(self, world, hud):
        super().__init__("GameManager")
        self.world = world
        self.hud = hud
        self.score = 0
        self.lives = 3
        self.state = "playing"
        self._respawn_t = 0
        self._moth_t = random.uniform(12, 20)
        self.player = None
        self.formation = None
    def _update(self, dt):
        if self.state == "gameover":
            if Input.is_action_just_pressed("confirm"): self._restart()
            return
        self._moth_t -= dt
        if self._moth_t <= 0:
            m = Mothership()
            m.died += self._on_mothership_died
            self.world += m
            self._moth_t = random.uniform(20, 30)
        if self.player and not self.player.alive:
            self._respawn_t -= dt
            if self._respawn_t <= 0: self._respawn()
        if self.formation and not [c for c in self.formation.children if isinstance(c, Enemy) and not c.dead]:
            self._next_wave()
    def _on_player_shot(self, pos):
        b = Bullet(pos, -1, "player")
        b.hit += self._on_bullet_hit
        self.world += b
    def _on_enemy_shot(self, pos):
        b = Bullet(pos, 1, "enemy")
        b.hit += self._on_bullet_hit
        self.world += b
    def _on_bullet_hit(self, target):
        if isinstance(target, Bullet):
            target.queue_free()
            return
        if isinstance(target, Player):
            target.hit()
        elif hasattr(target, "die"):
            target.die()
        elif hasattr(target, "take_damage"):
            target.take_damage()
    def _on_player_died(self, pos):
        self.lives -= 1
        self.hud.lives = self.lives
        if self.lives <= 0:
            self += Explosion(pos)
            self._game_over()
        else:
            self.world += Explosion(pos)
            self._respawn_t = 1.2
    def _on_enemy_died(self, enemy):
        self.score += enemy.score
        self.hud.score = self.score
        self.world += Explosion(enemy.global_position)
    def _on_mothership_died(self, moth):
        self.score += 100
        self.hud.score = self.score
        self.world += Explosion(moth.global_position)
    def _on_formation_bottom(self):
        self._game_over()
    def _respawn(self):
        if self.player:
            self.player.alive = True
            self.player.sprite.visible = True
            self.player.col.visible = True
            self.player.relative_pos = Vector2d(0, 250)
    def _game_over(self):
        if self.state == "gameover": return
        self.state = "gameover"
        self.hud.show_go = True
        for c in list(self.world.children):
            if c is not self.player: c.queue_free()
        if self.player:
            self.player.alive = False
            self.player.sprite.visible = False
            self.player.col.visible = False
    def _next_wave(self):
        if self.formation: self.formation.queue_free()
        self.formation = EnemyFormation()
        self.formation.speed = min(28 + self.score // 500, 70)
        self.formation.shot += self._on_enemy_shot
        self.formation.enemy_died += self._on_enemy_died
        self.formation.reached_bottom += self._on_formation_bottom
        self.world += self.formation
    def _restart(self):
        self.score = 0
        self.lives = 3
        self.state = "playing"
        self._moth_t = random.uniform(12, 20)
        self.hud.score = 0
        self.hud.lives = 3
        self.hud.show_go = False
        for c in list(self.world.children):
            if c is not self.player: c.queue_free()
        self.formation = EnemyFormation()
        self.formation.shot += self._on_enemy_shot
        self.formation.enemy_died += self._on_enemy_died
        self.formation.reached_bottom += self._on_formation_bottom
        self.world += self.formation
        for x in (-150, 0, 150):
            self.world += Shield(Vector2d(x, 180))
        self._respawn()
