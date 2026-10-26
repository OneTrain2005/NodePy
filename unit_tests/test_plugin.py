"""Unit tests for nodepy.Plugin and GameLoop plugin hooks"""

import pytest

from nodepy.GameLoop import GameLoop
from nodepy.Plugin import Plugin


class RecordingPlugin(Plugin):
    name = "recorder"

    def __init__(self):
        self.calls = []

    def on_install(self, loop):
        self.calls.append(("install", loop))

    def on_pre_process(self, delta):
        self.calls.append(("pre_process", delta))

    def on_post_physics(self, delta):
        self.calls.append(("post_physics", delta))

    def on_shutdown(self):
        self.calls.append(("shutdown",))

    def hooks(self):
        return [c[0] for c in self.calls]


class BrokenPlugin(Plugin):
    name = "broken"

    def on_pre_process(self, delta):
        raise RuntimeError("boom")


@pytest.fixture
def loop():
    gl = GameLoop(width=100, height=100)
    gl.root.withdraw()
    yield gl
    try:
        gl.root.destroy()
    except Exception:
        pass


class TestAddRemove:
    def test_add_calls_install_with_loop(self, loop):
        plugin = RecordingPlugin()
        assert loop.add_plugin(plugin) is plugin
        assert plugin.calls == [("install", loop)]

    def test_get_plugin_by_name(self, loop):
        plugin = loop.add_plugin(RecordingPlugin())
        assert loop.get_plugin("recorder") is plugin
        assert loop.get_plugin("missing") is None

    def test_duplicate_name_rejected(self, loop):
        loop.add_plugin(RecordingPlugin())
        with pytest.raises(ValueError):
            loop.add_plugin(RecordingPlugin())

    def test_remove_calls_shutdown(self, loop):
        plugin = loop.add_plugin(RecordingPlugin())
        loop.remove_plugin(plugin)
        assert plugin.hooks() == ["install", "shutdown"]
        assert loop.get_plugin("recorder") is None

    def test_remove_unknown_is_noop(self, loop):
        loop.remove_plugin(RecordingPlugin())

    def test_base_plugin_hooks_are_noops(self, loop):
        loop.add_plugin(Plugin())
        loop._tick()


class TestHooks:
    def test_pre_process_runs_each_tick(self, loop):
        plugin = loop.add_plugin(RecordingPlugin())
        loop._tick()
        assert "pre_process" in plugin.hooks()

    def test_post_physics_receives_fixed_delta(self, loop):
        plugin = loop.add_plugin(RecordingPlugin())
        loop._physics_accumulator = loop._physics_delta
        loop._last_time -= loop._physics_delta
        loop._tick()
        deltas = [c[1] for c in plugin.calls if c[0] == "post_physics"]
        assert deltas and all(d == loop._physics_delta for d in deltas)

    def test_broken_plugin_does_not_stop_others(self, loop, capsys):
        loop.add_plugin(BrokenPlugin())
        plugin = loop.add_plugin(RecordingPlugin())
        loop._tick()
        assert "pre_process" in plugin.hooks()
        assert "boom" in capsys.readouterr().err

    def test_run_shuts_plugins_down_on_exit(self, loop):
        plugin = loop.add_plugin(RecordingPlugin())
        loop.root.after(50, loop.root.destroy)
        loop.run()
        assert plugin.hooks()[-1] == "shutdown"
        assert loop.get_plugin("recorder") is None
