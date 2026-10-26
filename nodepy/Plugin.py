from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nodepy.GameLoop import GameLoop


class Plugin:
    """
    Base class for engine extensions that need to hook into the game loop.

    Plugins live in their own packages (e.g. ``nodepy-audio``) and are
    registered explicitly on a ``GameLoop``.  Override only the hooks you need;
    the defaults do nothing.

    Plugins that only add new Node types don't need this — subclassing
    ``Node`` is enough.  Use a Plugin for engine-wide services such as an
    audio mixer that must be pumped every frame or closed on exit.

    Usage
    -----
    class AudioServer(Plugin):
        name = "audio"
        def on_install(self, loop): self.mixer = open_device()
        def on_shutdown(self):      self.mixer.close()

    loop = GameLoop()
    loop.add_plugin(AudioServer())
    """

    name: str = "unnamed"

    def on_install(self, loop: GameLoop) -> None:
        """Called once from ``GameLoop.add_plugin``. ``loop.root`` and ``loop.canvas`` exist."""

    def on_pre_process(self, delta: float) -> None:
        """Called every frame, before the scene's ``_process``."""

    def on_post_physics(self, delta: float) -> None:
        """Called after every fixed physics step, once collisions are resolved."""

    def on_shutdown(self) -> None:
        """Called once when the loop stops or the plugin is removed."""
