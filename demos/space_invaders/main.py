"""
Demo scene for NodePy. Built with NodePy version 1.1

It's a space invaders clone.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from Engine.GameLoop import GameLoop
from Engine.Camera2D import Camera2D
from Engine.Input import Input
from Engine.Node import Node
from Engine.TextureManager import TextureManager
from Engine.Vector2d import Vector2d
from PIL import Image
from constants import *
from player import Player
from enemy import EnemyFormation
from shield import Shield
from hud import HUD
from game_manager import GameManager

Input.add_action("shoot", ["space"])

def build_scene(loop):
    root = Node("Root")
    world = Node("World")
    root += world
    cam = Camera2D("Camera", viewport_size=(loop.width, loop.height), zoom=1.0)
    root += cam
    cam.make_active()
    hud = HUD()
    root += hud
    gm = GameManager(world, hud)
    root += gm
    player = Player()
    world += player
    gm.player = player
    player.shot += gm._on_player_shot
    player.died += gm._on_player_died
    for x in (-150, 0, 150):
        world += Shield(Vector2d(x, 180))
    formation = EnemyFormation()
    world += formation
    gm.formation = formation
    formation.shot += gm._on_enemy_shot
    formation.enemy_died += gm._on_enemy_died
    formation.reached_bottom += gm._on_formation_bottom
    for tex in (PLAYER, SMALL, MED, BIG, MOTH, SHIELD, BOOM):
        TextureManager.instance().prewarm(tex, tex.width, tex.height, Image.NEAREST)
    return root

if __name__ == "__main__":
    loop = GameLoop(800, 600, "Space Invaders — NodePy", bg="#050505")
    loop.set_scene(build_scene(loop))
    loop.run()
