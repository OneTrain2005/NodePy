from __future__ import annotations
from typing import Callable, List

class Signal:
    """
    Godot-style signal.

    Usage
    -----
    class MyNode(Node):
        def __init__(self):
            super().__init__("MyNode")
            self.hit = Signal("hit")           # declare
            self.hit.connect(self._on_hit)     # connect

        def take_damage(self):
            self.hit.emit(self, 10)            # emit with args
    """

    def __init__(self, name: str = ""):
        self.name = name
        self._listeners: List[Callable] = []

    def connect(self, callback: Callable) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def disconnect(self, callback: Callable) -> None:
        self._listeners = [cb for cb in self._listeners if cb is not callback]

    def emit(self, *args, **kwargs) -> None:
        for cb in list(self._listeners):
            cb(*args, **kwargs)

    def __call__(self, *args, **kwargs) -> None:
        self.emit(*args, **kwargs)

    def __iadd__(self, callback: Callable) -> "Signal":
        self.connect(callback)
        return self

    def __isub__(self, callback: Callable) -> "Signal":
        self.disconnect(callback)
        return self

    def __repr__(self) -> str:
        return f"Signal({self.name!r}, {len(self._listeners)} listeners)"