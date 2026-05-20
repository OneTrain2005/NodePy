"""Unit tests for Engine.Signal"""

import pytest
from Engine.Signal import Signal


class TestSignalConnect:
    def test_connect_adds_listener(self):
        sig = Signal("test")
        called = []
        sig.connect(lambda *a, **k: called.append(True))
        sig.emit()
        assert len(called) == 1

    def test_connect_does_not_duplicate(self):
        sig = Signal("test")
        called = []
        fn = lambda *a, **k: called.append(True)
        sig.connect(fn)
        sig.connect(fn)
        sig.emit()
        assert len(called) == 1

    def test_connect_multiple_different_listeners(self):
        sig = Signal("test")
        results = []
        sig.connect(lambda: results.append(1))
        sig.connect(lambda: results.append(2))
        sig.emit()
        assert sorted(results) == [1, 2]


class TestSignalDisconnect:
    def test_disconnect_removes_listener(self):
        sig = Signal("test")
        called = []
        fn = lambda *a, **k: called.append(True)
        sig.connect(fn)
        sig.disconnect(fn)
        sig.emit()
        assert len(called) == 0

    def test_disconnect_unknown_is_noop(self):
        sig = Signal("test")
        sig.disconnect(lambda: None)  # never connected
        sig.emit()  # should not raise

    def test_disconnect_only_targeted_listener(self):
        sig = Signal("test")
        results = []
        fn_a = lambda: results.append("a")
        fn_b = lambda: results.append("b")
        sig.connect(fn_a)
        sig.connect(fn_b)
        sig.disconnect(fn_a)
        sig.emit()
        assert results == ["b"]


class TestSignalEmit:
    def test_emit_no_args(self):
        sig = Signal("test")
        called = []
        sig.connect(lambda: called.append(True))
        sig.emit()
        assert len(called) == 1

    def test_emit_with_positional_args(self):
        sig = Signal("test")
        received = []
        sig.connect(lambda a, b: received.append((a, b)))
        sig.emit(1, 2)
        assert received == [(1, 2)]

    def test_emit_with_kwargs(self):
        sig = Signal("test")
        received = []
        sig.connect(lambda **kw: received.append(kw))
        sig.emit(x=3, y=4)
        assert received == [{"x": 3, "y": 4}]

    def test_emit_mixed_args(self):
        sig = Signal("test")
        received = []
        sig.connect(lambda a, b, **kw: received.append((a, b, kw)))
        sig.emit(1, 2, flag=True)
        assert received == [(1, 2, {"flag": True})]

    def test_emit_order_preserved(self):
        sig = Signal("test")
        order = []
        sig.connect(lambda: order.append(1))
        sig.connect(lambda: order.append(2))
        sig.connect(lambda: order.append(3))
        sig.emit()
        assert order == [1, 2, 3]


class TestSignalRepr:
    def test_repr_empty(self):
        sig = Signal("health_changed")
        assert repr(sig) == "Signal('health_changed', 0 listeners)"

    def test_repr_with_listeners(self):
        sig = Signal("health_changed")
        sig.connect(lambda: None)
        assert repr(sig) == "Signal('health_changed', 1 listeners)"
