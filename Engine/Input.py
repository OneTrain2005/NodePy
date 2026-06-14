from __future__ import annotations
from Engine.Vector2d import Vector2d
from typing import Callable, Dict, List
import tkinter as tk

class Input:
    """
    Singleton input manager.  Query state each frame; do not store references
    to events — they are cleared at the start of every frame.

    Keys
    ----
    Input.is_action_pressed("move_right")   # held this frame
    Input.is_action_just_pressed("jump")    # pressed this frame only
    Input.is_action_just_released("jump")   # released this frame only

    Mouse
    -----
    Input.mouse_position()      Vector2d in screen space
    Input.is_mouse_pressed(1)   # 1=left, 2=middle, 3=right
    Input.mouse_just_pressed(1)
    Input.mouse_just_released(1)

    Action map (add before running):
        Input.add_action("move_right", ["Right", "d"])
    """

    # Default action → key bindings
    _action_map: Dict[str, List[str]] = {
        "move_left":  ["Left", "a"],
        "move_right": ["Right", "d"],
        "move_up":    ["Up", "w"],
        "move_down":  ["Down", "s"],
        "jump":       ["space"],
        "confirm":    ["Return"],
        "cancel":     ["Escape"],
    }

    _held:          set = set()   # keys currently down
    _just_pressed:  set = set()   # keys pressed this frame
    _just_released: set = set()   # keys released this frame

    _mouse_pos: Vector2d                   = Vector2d()
    _mouse_held:          set              = set()
    _mouse_just_pressed:  set              = set()
    _mouse_just_released: set              = set()

    # ── Internal hooks called by GameLoop ────────────────────────────────────

    @classmethod
    def _on_key_press(cls, event: tk.Event) -> None:
        key = event.keysym
        if key not in cls._held:
            cls._just_pressed.add(key)
        cls._held.add(key)

    @classmethod
    def _on_key_release(cls, event: tk.Event) -> None:
        key = event.keysym
        cls._held.discard(key)
        cls._just_released.add(key)

    @classmethod
    def _on_mouse_move(cls, event: tk.Event) -> None:
        cls._mouse_pos = Vector2d(event.x, event.y)

    @classmethod
    def _on_mouse_press(cls, event: tk.Event) -> None:
        cls._mouse_held.add(event.num)
        cls._mouse_just_pressed.add(event.num)

    @classmethod
    def _on_mouse_release(cls, event: tk.Event) -> None:
        cls._mouse_held.discard(event.num)
        cls._mouse_just_released.add(event.num)

    @classmethod
    def _on_focus_out(cls, event: tk.Event) -> None:
        """Clear all input state when the window loses focus.
        Prevents keys getting stuck if the OS swallows KeyRelease events."""
        cls._held.clear()
        cls._just_pressed.clear()
        cls._just_released.clear()
        cls._mouse_held.clear()
        cls._mouse_just_pressed.clear()
        cls._mouse_just_released.clear()

    @classmethod
    def _flush(cls) -> None:
        """Clear per-frame state.  Called at the START of each frame."""
        cls._just_pressed.clear()
        cls._just_released.clear()
        cls._mouse_just_pressed.clear()
        cls._mouse_just_released.clear()

    # ── Public API ───────────────────────────────────────────────────────────

    @classmethod
    def add_action(cls, name: str, keys: List[str]) -> None:
        cls._action_map[name] = keys

    @classmethod
    def _keys_for(cls, action: str) -> List[str]:
        return cls._action_map.get(action, [action])

    @classmethod
    def is_action_pressed(cls, action: str) -> bool:
        return any(k in cls._held for k in cls._keys_for(action))

    @classmethod
    def is_action_just_pressed(cls, action: str) -> bool:
        return any(k in cls._just_pressed for k in cls._keys_for(action))

    @classmethod
    def is_action_just_released(cls, action: str) -> bool:
        return any(k in cls._just_released for k in cls._keys_for(action))

    @classmethod
    def get_axis(cls, negative_action: str, positive_action: str) -> float:
        """Returns -1, 0, or 1 — convenient for movement."""
        return float(cls.is_action_pressed(positive_action)) \
             - float(cls.is_action_pressed(negative_action))

    @classmethod
    def get_vector(cls, left: str, right: str,
                   up: str, down: str) -> Vector2d:
        """Returns a (possibly un-normalised) direction vector from four actions."""
        return Vector2d(cls.get_axis(left, right), cls.get_axis(up, down))

    @classmethod
    def mouse_position(cls) -> Vector2d:
        return cls._mouse_pos

    @classmethod
    def is_mouse_pressed(cls, button: int = 1) -> bool:
        return button in cls._mouse_held

    @classmethod
    def mouse_just_pressed(cls, button: int = 1) -> bool:
        return button in cls._mouse_just_pressed

    @classmethod
    def mouse_just_released(cls, button: int = 1) -> bool:
        return button in cls._mouse_just_released