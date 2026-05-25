# NodePy 🪢🥧

A Godot-inspired 2D game engine built in Python and tkinter. One external dependency — Pillow — for image textures. Everything else is pure standard library.

This README will walk you through **how to use** the engine and **how it works under the hood** — including the software design patterns that make it tick, with links to deeper reading for each one.

---

## Table of contents

1. [Getting started](#getting-started)
2. [Project structure](#project-structure)
3. [Core concepts](#core-concepts)
   - [The scene tree](#the-scene-tree)
   - [The transform pipeline](#the-transform-pipeline)
   - [The game loop](#the-game-loop)
4. [Using the engine](#using-the-engine)
   - [Creating nodes](#creating-nodes)
   - [Signals](#signals)
   - [Input](#input)
   - [ColorRect2D](#colorrect2d)
   - [Sprite2D](#sprite2d)
   - [CollisionShape](#collisionshape)
   - [Camera2D](#camera2d)
5. [Design patterns used](#design-patterns-used)
6. [Contributing](#contributing)

---

## Getting started

Make sure you have **Python 3.10+** and **Pillow** installed. tkinter ships with Python on most platforms — if it is missing, install it with your package manager:
- `sudo apt install python3-tk` on Debian based OS
- `sudo pacman -S tk` on Arch based OS

Install Pillow:

```bash
pip install Pillow
```

Clone the repo and run a demo:

```bash
git clone https://github.com/OneTrain2005/NodePy.git
cd NodePy
python3 demos/coin_collector/main.py
```

You should see a window with a player square you can move with **WASD** or the **arrow keys**, and spinning textured coins to collect.

There is also a **space invaders** demo:

```bash
python3 demos/space_invaders/main.py
```

---

## Project structure

```
.
├── Engine
│   ├── Camera2D.py         # Viewport camera with zoom and smooth follow
│   ├── CollisionShape.py   # AABB hit detection + body_entered / body_exited
│   ├── ColorRect2D.py      # Solid-colour rectangle in world space
│   ├── GameLoop.py         # Owns the window, drives update + render each frame
│   ├── Input.py            # Keyboard and mouse state, polled per frame
│   ├── Matrix3x3.py        # Homogeneous 2D transform math (TRS)
│   ├── Node.py             # Base class for every object in the scene
│   ├── Quadtree.py         # Spatial partitioning for broadphase collision
│   ├── Signal.py           # Lightweight event system
│   ├── Sprite2D.py         # Textured sprite with rotation, scale, and camera zoom
│   ├── Texture2D.py        # PIL image wrapper + file loading cache
│   ├── TextureManager.py   # LRU cache of baked PhotoImages (resize + rotate)
│   └── Vector2d.py         # 2D vector with arithmetic helpers
├── demos
│   ├── coin_collector/     # WASD movement, camera follow, textured coins
│   └── space_invaders/     # Full mini-game with sprites, shields, enemies
├── unit_tests/             # pytest suite
├── LICENSE                 # MIT LICENSE, this project is open source
└── README.md               # Read it
```

---

## Core concepts

### The scene tree

Everything in the engine is a **Node**. Nodes are arranged in a tree: each node has one parent and any number of children. This is the same structure used by Godot, Unity (GameObjects), and most other game engines.

```
Root
├── World
│   ├── Player
│   │   ├── ColorRect2D   (visual)
│   │   └── CollisionShape (hitbox)
│   ├── Coin
│   │   ├── Sprite2D      (textured visual)
│   │   └── CollisionShape
│   └── Camera2D
└── HUD  (screen-space UI, lives outside World)
```

A child node's position, rotation, and scale are always **relative to its parent**. Move the parent and all children follow automatically. This is called a **local transform** and it is computed through matrix multiplication (more on that below).

### The transform pipeline

Every node stores three properties: `relative_pos`, `rotation`, and `scale`. These are combined into a single **3×3 matrix** (a standard technique for 2D and 3D transforms that lets you compose any combination of translate, rotate, and scale through matrix multiplication).

When you ask for a node's position in the world, the engine walks up the tree and multiplies all the local matrices together:

```
global_matrix = parent.global_matrix × local_matrix
```

The result gives you the node's true position, rotation, and scale in world space. The key insight is that **you never have to do this manually** — just set `relative_pos` on a child and the math happens automatically.

The engine uses a **dirty flag** to avoid recomputing transforms every frame. When you change a property, the node marks itself and all its descendants as dirty. The transform is only recalculated the next time it is actually needed.

### The game loop

Each frame, `GameLoop` does four things in order:

```
1. Input._flush()               clear "just pressed" state from last frame
2. rebuild Quadtree             spatial index of all CollisionShapes
3. scene._process(delta)        call _update(delta) on every node, top to bottom
4. scene._render(canvas)        call _draw(canvas, camera) on every node, top to bottom
```

`delta` is the number of seconds since the last frame (typically around 0.016 for 60 fps). **Always multiply movement and time-based values by delta** — this makes your game run at the same speed regardless of frame rate.

```python
# BAD — speed depends on frame rate
self.relative_pos.x += 5

# GOOD — 300 pixels per second, any frame rate
self.relative_pos = self.relative_pos + Vector2d(300 * delta, 0)
```

---

## Using the engine

### Creating nodes

Import what you need from the `Engine` package and subclass `Node`:

```python
from Engine.Node import Node
from Engine.Vector2d import Vector2d

class MyObject(Node):
    def __init__(self):
        super().__init__("MyObject")

    def _ready(self):
        # Called once when this node enters the scene tree.
        print(f"{self.name} is ready!")

    def _update(self, delta: float):
        # Called every frame. delta = seconds since last frame.
        self.rotation = self.rotation + 45 * delta  # rotate 45°/sec

    def _draw(self, canvas, cam):
        # Called every frame for custom drawing.
        # cam is the camera matrix — multiply it onto your global_matrix
        # before drawing so the camera works correctly.
        pass
```

Build a scene and hand it to the `GameLoop`:

```python
from Engine.GameLoop import GameLoop
from Engine.Node import Node
from Engine.Vector2d import Vector2d

root = Node("Root")
obj  = MyObject()
root.add_child(obj)
obj.relative_pos = Vector2d(200, 150)

loop = GameLoop(width=800, height=600, title="My Game")
loop.set_scene(root)
loop.run()
```

**Node lifecycle at a glance:**

| Method | When it runs |
|---|---|
| `__init__` | When the object is constructed in Python |
| `_ready()` | Once, when `add_child()` connects it to an active tree |
| `_update(delta)` | Every frame, before drawing |
| `_draw(canvas, cam)` | Every frame, after all updates |

You can toggle a node (and all its children) off completely:

```python
coin.visible = False   # stops _update and _draw for the whole subtree
```

You can also safely delete a node from inside its own `_update`:

```python
self.queue_free()   # removed at the end of the current frame
```

**Tree sugar:**

```python
# Add / remove with operators
world += player       # same as world.add_child(player)
world -= player       # same as world.remove_child(player)

# Access children by name or index
player = world["Player"]
first  = world[0]

# Check membership
if "Player" in world:
    ...
```

### Signals

A `Signal` is a way for one node to tell other nodes that something happened, **without needing to know who is listening**. Think of it like a radio broadcast: the sender emits, anyone who tuned in receives.

```python
from Engine.Node import Node
from Engine.Signal import Signal

class Door(Node):
    def __init__(self):
        super().__init__("Door")
        self.opened = Signal("opened")   # declare the signal

    def open(self):
        print("Door opens!")
        self.opened.emit(self)           # broadcast to all listeners

class SoundManager(Node):
    def __init__(self, door: Door):
        super().__init__("SoundManager")
        door.opened.connect(self._on_door_opened)   # subscribe

    def _on_door_opened(self, door):
        print("Playing creak sound...")
```

You can connect multiple listeners to the same signal, and one listener can connect to signals from many different nodes. To stop listening:

```python
door.opened.disconnect(self._on_door_opened)
```

`CollisionShape` ships with two built-in signals:

```python
col.body_entered.connect(self._on_hit)   # another shape just started overlapping
col.body_exited.connect(self._on_leave)  # it stopped overlapping
```

### Input

`Input` is a class you query each frame — you never instantiate it. `GameLoop` feeds it keyboard and mouse events automatically.

```python
from Engine.Input import Input

def _update(self, delta):
    # Held keys
    if Input.is_action_pressed("move_right"):
        self.relative_pos = self.relative_pos + Vector2d(200 * delta, 0)

    # Single-frame events (only True for one frame)
    if Input.is_action_just_pressed("jump"):
        self.velocity_y = -400

    # Axis: returns -1, 0, or +1
    h = Input.get_axis("move_left", "move_right")
    v = Input.get_axis("move_up",   "move_down")

    # Vector: combines two axes into one direction
    direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
```

**Default action bindings:**

| Action | Keys |
|---|---|
| `move_left` | Left arrow, A |
| `move_right` | Right arrow, D |
| `move_up` | Up arrow, W |
| `move_down` | Down arrow, S |
| `jump` | Space |
| `confirm` | Enter |
| `cancel` | Escape |

Add your own bindings before the loop starts:

```python
Input.add_action("shoot", ["f", "Control_L"])
```

Mouse:

```python
pos = Input.mouse_position()            # Vector2d in screen space
if Input.is_mouse_pressed(1):           # 1=left, 2=middle, 3=right
    print(f"Click at {pos.x}, {pos.y}")
if Input.mouse_just_released(1):
    print("Released")
```

### ColorRect2D

`ColorRect2D` draws a solid-colour rectangle at the node's world position. It inherits the full transform pipeline, so it rotates, scales, and moves with its parent automatically.

```python
from Engine.ColorRect2D import ColorRect2D
from Engine.Vector2d import Vector2d

class Player(Node):
    def __init__(self):
        super().__init__("Player")

        # A 32×32 yellow square, centred on this node's origin
        self.sprite = ColorRect2D(
            "sprite",
            width=32, height=32,
            color="#f6c90e",
            outline="#ffd700",
            label="Player",   # optional text at the centre
            parent=self,
        )

    def _update(self, delta):
        # Rotating the sprite rotates it around the Player node's origin
        self.sprite.rotation = self.sprite.rotation + 90 * delta
```

Because `ColorRect2D` is just a `Node`, you can nest them inside each other to build composite visuals — a body with separately rotating arms, for example.

### Sprite2D

`Sprite2D` draws a **texture** (a `Texture2D` image) in world space. Rotation, scale, and camera zoom are all baked into a cached `PhotoImage` by the `TextureManager`, so sprites look crisp at any angle and zoom level.

```python
from PIL import Image
from Engine.Sprite2D import Sprite2D
from Engine.Texture2D import ImageTexture

class Coin(Node):
    def __init__(self):
        super().__init__("Coin")

        # Load from disk — cached by path so the same file is never read twice
        texture = ImageTexture.load("coin.png", native_size=(24, 24))

        self.sprite = Sprite2D(
            "sprite",
            texture=texture,
            width=24, height=24,
            filter_mode=Image.NEAREST,   # pixel-art look, fastest bake
            parent=self,
        )

    def _update(self, delta):
        self.sprite.rotation = self.sprite.rotation + 120 * delta
```

**Prewarming** — if you know a sprite will spin or zoom, bake every rotation frame up front so no PIL work happens during gameplay:

```python
from Engine.TextureManager import TextureManager

TextureManager.instance().prewarm(texture, w_px=24, h_px=24, filter_mode=Image.NEAREST)
```

### CollisionShape

`CollisionShape` gives a node an **axis-aligned bounding box** (AABB) for hit detection. The box is automatically recalculated from the node's current global transform every time it is checked.

```python
from Engine.CollisionShape import CollisionShape

class Enemy(Node):
    def __init__(self):
        super().__init__("Enemy")

        self.sprite = ColorRect2D("sprite", 24, 24, color="red", parent=self)
        self.col    = CollisionShape(
            "col",
            width=24, height=24,
            debug_draw=True,   # draws a dashed green outline — useful while building
            parent=self,
        )
        self.col.body_entered.connect(self._on_hit)

    def _on_hit(self, other: CollisionShape):
        print(f"{self.name} was hit by {other.parent.name}!")
```

Collision detection uses a **quadtree** for broadphase: each frame `GameLoop` rebuilds a spatial index, and each `CollisionShape` only checks shapes that are nearby. This scales far better than the old O(n²) scan. Turn off `debug_draw` once you are done testing.

You can also check a single point (handy for mouse interaction):

```python
if self.col.contains_point(Input.mouse_position()):
    print("Mouse is over this object")
```

### Camera2D

`Camera2D` moves the viewport so a world position stays centred on screen. Make one active and the `GameLoop` will use it automatically. The canvas now resizes with the window, and the camera viewport stays in sync.

```python
from Engine.Camera2D import Camera2D
from Engine.Vector2d import Vector2d

camera = Camera2D(
    "Camera2D",
    viewport_size=(800, 600),
    zoom=1.5,            # 1.5× magnification
    offset=Vector2d(0, -40),   # aim slightly above centre
    parent=world,
)
camera.make_active()
```

For a smooth follow camera, subclass `Camera2D` and lerp toward the target each frame:

```python
class SmoothCamera(Camera2D):
    def __init__(self, target: Node, viewport_size):
        super().__init__("Camera2D", viewport_size=viewport_size)
        self.target = target

    def _update(self, delta):
        tp = self.target.global_position
        cp = self.global_position
        speed = 5.0
        nx = cp.x + (tp.x - cp.x) * min(1.0, speed * delta)
        ny = cp.y + (tp.y - cp.y) * min(1.0, speed * delta)
        self.relative_pos = Vector2d(nx, ny)
```

For HUD elements that should stay fixed on screen regardless of the camera, attach them to the **root node** rather than the world node. The HUD node's `_draw` method can simply ignore the `cam` matrix and draw directly in screen coordinates.

---

## Design patterns used

One of the goals of this engine is to demonstrate how well-known software design patterns solve real problems. Here is where each one appears and why it was chosen.

---

### Composite — the scene tree

> [refactoring.guru/design-patterns/composite](https://refactoring.guru/design-patterns/composite)

The Composite pattern lets you treat a single object and a group of objects the same way. In this engine, every `Node` — whether it is a leaf (`Sprite2D`) or a branch (a `Player` with children) — responds to the same methods: `_update(delta)`, `_draw(canvas, cam)`, `add_child()`.

When `GameLoop` calls `root._process(delta)`, it does not need to know the shape of the tree. Each node calls `_process` on its own children recursively. You can nest nodes as deep as you like and the loop never changes.

```python
def _process(self, delta):
    self._update(delta)              # my own logic
    for child in self.children:
        child._process(delta)        # delegate to subtree
```

This is why you can drop a `SmoothCamera` anywhere in the tree and it just works — it is a node like everything else.

---

### Observer — signals

> [refactoring.guru/design-patterns/observer](https://refactoring.guru/design-patterns/observer)

The Observer pattern defines a one-to-many relationship: when one object changes state, all its dependents are notified automatically. This is exactly what `Signal` does.

Without this pattern you might write:

```python
# Tightly coupled — Player must know about HUD, SoundManager, SaveSystem...
def collect_coin(self):
    self.hud.increment_score()
    self.sound.play("coin")
    self.save.mark_collected(self)
```

With signals:

```python
# Player knows nothing about who is listening
def collect_coin(self):
    self.score += 1
    self.coin_collected.emit(self.score)  # just broadcast
```

The HUD, sound manager, and save system each connect to `coin_collected` independently. Adding a new system (e.g. an achievement tracker) requires zero changes to `Player`.

---

### Template method — the node lifecycle

> [refactoring.guru/design-patterns/template-method](https://refactoring.guru/design-patterns/template-method)

The Template Method pattern defines the skeleton of an algorithm in a base class and lets subclasses fill in specific steps. The base `Node` class defines *when* `_ready`, `_update`, and `_draw` are called. Your subclass defines *what* they do.

```python
# Base class (engine) — defines the skeleton
class Node:
    def _process(self, delta):
        self._update(delta)          # <-- subclass fills this in
        for child in self.children:
            child._process(delta)

    def _update(self, delta):
        pass                         # default: do nothing
```

```python
# Your class — fills in the step
class Coin(Node):
    def _update(self, delta):
        self.sprite.rotation += 120 * delta   # spin!
```

You never call `_update` directly — the engine calls it for you at the right time. This is the same model used by Unity (`Update()`), Godot (`_process()`), and most other engines.

---

### Singleton — Input, TextureManager, and CollisionShape registry

> [refactoring.guru/design-patterns/singleton](https://refactoring.guru/design-patterns/singleton)

The Singleton pattern ensures that only one instance of a class exists and provides a global point of access to it. `Input` uses class-level attributes and methods so there is effectively one shared state for the entire program — any node can call `Input.is_action_pressed(...)` without passing an object around.

```python
# No instance needed — state lives on the class itself
if Input.is_action_just_pressed("jump"):
    self.jump()
```

`TextureManager` is a lazily-created singleton that owns every `PhotoImage` the engine bakes. If the Python `PhotoImage` object were garbage-collected, tkinter would silently stop drawing it; the manager prevents that by keeping the sole long-lived reference.

`CollisionShape` uses a similar approach for its `_all` registry: a class-level list that every shape registers into when created, so they can find each other without a central manager object.

The trade-off is that singletons make testing harder (global state is harder to isolate) and can hide dependencies. This is why experienced engineers use them sparingly and only for truly global concepts like input, texture caching, or a renderer.

---

### Dirty flag — transform caching

> [Mentioned in Game Programming Patterns — Robert Nystrom](https://gameprogrammingpatterns.com/dirty-flag.html) *(not a GoF pattern, but widely used in game engines)*

A dirty flag avoids recomputing expensive results when nothing has changed. Every `Node` has a `_dirty` boolean. When you set `rotation`, the setter marks the node and all its descendants dirty. The global matrix is only recalculated the next time it is actually read.

```python
@rotation.setter
def rotation(self, value):
    self._rotation = value
    self.invalidate()          # mark self + all children dirty

def invalidate(self):
    if self._dirty:
        return                 # already dirty, no need to recurse again
    self._dirty = True
    for child in self.children:
        child.invalidate()
```

In a scene with hundreds of nodes, most transforms are unchanged most frames. Without this optimisation, every node would recompute its global matrix every frame even if nothing moved.

---

### Strategy — Camera2D

> [refactoring.guru/design-patterns/strategy](https://refactoring.guru/design-patterns/strategy)

The Strategy pattern lets you swap out an algorithm at runtime. `Camera2D` is the base strategy: `GameLoop` calls `camera.get_view_matrix()` without caring what kind of camera it is. By subclassing `Camera2D` and overriding `_update`, you can plug in a lerp camera, a shake camera, a cutscene camera, or anything else — and the `GameLoop` never changes.

```python
# GameLoop only knows about Camera2D — not the specific subclass
def _get_view_matrix(self):
    cam = Camera2D._active
    if cam is not None:
        return cam.get_view_matrix()   # calls whatever subclass defines
    return Matrix3x3()
```

---

## Contributing

This engine is intentionally small and incomplete. That is a feature, not a bug — there is a lot of room to grow, and this codebase is simple enough that you can actually understand all of it.

Here are some things that are genuinely missing and would make great first contributions:

- **`AnimatedSprite2D`** — cycle through frames with a configurable FPS
- **`RigidBody2D`** — velocity, gravity, and basic physics resolution
- **`TileMap`** — render a grid of tiles from a tile sheet
- **`AudioNode`** — play `.wav` files using the `wave` + `tkinter` audio modules
- **Scene serialisation** — save and load a scene tree to/from JSON
- **A GUI editor** — a second tkinter window that lets you place and configure nodes visually and save scenes to disk

If you want to contribute:

1. Fork the repo on GitHub
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes — try to match the existing code style (properties with setters, docstrings, type hints)
4. Test it by building something small in `demos/` that uses the new feature
5. Open a pull request with a short description of what you added and why

No contribution is too small. Fixing a typo in a docstring, adding a missing type hint, or writing a better code example in this README are all welcome.

You can run the unit tests of this repo by using the `python -m pytest unit_tests/ -v` command.  
You can also write your own unit tests with pytest.

If you are not sure where to start, open an issue describing what you want to build and we can figure it out together.
