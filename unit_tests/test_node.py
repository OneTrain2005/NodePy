"""Unit tests for Engine.Node"""

import pytest
from Engine.Node import Node
from Engine.Vector2d import Vector2d
from Engine.Matrix3x3 import Matrix3x3


class TestNodeInit:
    def test_default_init(self):
        n = Node("root")
        assert n.name == "root"
        assert n.parent is None
        assert n.children == []
        assert n.visible is True

    def test_init_with_parent(self):
        parent = Node("parent")
        child = Node("child", parent=parent)
        assert child.parent is parent
        assert child in parent.children

    def test_init_with_relative_pos(self):
        n = Node("n", relative_pos=Vector2d(10, 20))
        assert n.relative_pos.x == 10
        assert n.relative_pos.y == 20

    def test_default_scale_is_one(self):
        n = Node("n")
        assert n.scale.x == 1.0
        assert n.scale.y == 1.0

    def test_default_rotation_is_zero(self):
        n = Node("n")
        assert n.rotation == 0.0


class TestNodeTreeManagement:
    def test_add_child_sets_parent(self):
        p = Node("p")
        c = Node("c")
        p.add_child(c)
        assert c.parent is p

    def test_add_child_appends_to_children(self):
        p = Node("p")
        c1 = Node("c1")
        c2 = Node("c2")
        p.add_child(c1)
        p.add_child(c2)
        assert p.children == [c1, c2]

    def test_add_child_reparents(self):
        p1 = Node("p1")
        p2 = Node("p2")
        c = Node("c", parent=p1)
        p2.add_child(c)
        assert c.parent is p2
        assert c not in p1.children

    def test_remove_child(self):
        p = Node("p")
        c = Node("c", parent=p)
        p.remove_child(c)
        assert c.parent is None
        assert c not in p.children

    def test_remove_non_child_is_noop(self):
        p = Node("p")
        c = Node("c")
        p.remove_child(c)  # should not raise
        assert c.parent is None

    def test_get_child_by_name(self):
        p = Node("p")
        c = Node("target", parent=p)
        assert p.get_child("target") is c

    def test_get_child_missing_returns_none(self):
        p = Node("p")
        assert p.get_child("missing") is None


class TestNodePropertiesInvalidate:
    def test_relative_pos_setter_invalidates(self):
        n = Node("n")
        n._dirty = False
        n.relative_pos = Vector2d(1, 1)
        assert n._dirty is True

    def test_rotation_setter_invalidates(self):
        n = Node("n")
        n._dirty = False
        n.rotation = 45.0
        assert n._dirty is True

    def test_scale_setter_invalidates(self):
        n = Node("n")
        n._dirty = False
        n.scale = Vector2d(2, 2)
        assert n._dirty is True


class TestNodeInvalidatePropagates:
    def test_invalidate_propagates_to_children(self):
        p = Node("p")
        c = Node("c", parent=p)
        gc = Node("gc", parent=c)
        p._dirty = False
        c._dirty = False
        gc._dirty = False
        p.invalidate()
        assert p._dirty is True
        assert c._dirty is True
        assert gc._dirty is True

    def test_invalidate_idempotent(self):
        p = Node("p")
        c = Node("c", parent=p)
        p.invalidate()
        # Second call should not cause issues
        p.invalidate()
        assert p._dirty is True
        assert c._dirty is True


class TestNodeTransform:
    def test_global_matrix_identity_at_origin(self):
        n = Node("n")
        mat = n.global_matrix
        assert mat.multiply_vec(0, 0) == (0, 0)

    def test_global_matrix_with_translation(self):
        n = Node("n", relative_pos=Vector2d(10, 20))
        x, y = n.global_matrix.multiply_vec(0, 0)
        assert x == pytest.approx(10.0)
        assert y == pytest.approx(20.0)

    def test_global_matrix_parent_chain(self):
        p = Node("p", relative_pos=Vector2d(10, 0))
        c = Node("c", relative_pos=Vector2d(5, 0), parent=p)
        x, y = c.global_matrix.multiply_vec(0, 0)
        assert x == pytest.approx(15.0)
        assert y == pytest.approx(0.0)

    def test_global_matrix_with_rotation(self):
        n = Node("n", relative_pos=Vector2d(0, 0))
        n.rotation = 90
        # 90° clockwise in screen space: (1,0) -> (0,1)
        x, y = n.global_matrix.multiply_vec(1, 0)
        assert x == pytest.approx(0.0, abs=1e-9)
        assert y == pytest.approx(1.0, abs=1e-9)

    def test_global_matrix_with_scale(self):
        n = Node("n")
        n.scale = Vector2d(2, 3)
        x, y = n.global_matrix.multiply_vec(1, 1)
        assert x == pytest.approx(2.0)
        assert y == pytest.approx(3.0)

    def test_dirty_flag_cleared_after_update(self):
        n = Node("n")
        _ = n.global_matrix
        assert n._dirty is False

    def test_global_position_property(self):
        n = Node("n", relative_pos=Vector2d(100, -50))
        pos = n.global_position
        assert pos.x == pytest.approx(100.0)
        assert pos.y == pytest.approx(-50.0)


class TestNodeSignals:
    def test_tree_entered_emitted_on_add_child(self):
        p = Node("p")
        received = []
        c = Node("c")
        c.tree_entered.connect(lambda node: received.append(node.name))
        p.add_child(c)
        assert received == ["c"]

    def test_tree_exited_emitted_on_remove_child(self):
        p = Node("p")
        c = Node("c", parent=p)
        received = []
        c.tree_exited.connect(lambda node: received.append(node.name))
        p.remove_child(c)
        assert received == ["c"]


class TestNodeReady:
    def test_ready_called_once(self):
        class CounterNode(Node):
            def __init__(self):
                super().__init__("counter")
                self.count = 0

            def _ready(self):
                self.count += 1

        n = CounterNode()
        n._call_ready()
        assert n.count == 1
        # _call_ready does not guard itself; it guards children via _ready_called
        n._call_ready()
        assert n.count == 2

    def test_ready_propagates_to_children(self):
        class CounterNode(Node):
            def __init__(self):
                super().__init__("counter")
                self.count = 0

            def _ready(self):
                self.count += 1

        p = CounterNode()
        c = CounterNode()
        p.add_child(c)
        p._call_ready()
        assert p.count == 1
        assert c.count == 1

    def test_add_child_to_ready_parent_calls_ready(self):
        class CounterNode(Node):
            def __init__(self):
                super().__init__("counter")
                self.count = 0

            def _ready(self):
                self.count += 1

        p = CounterNode()
        p._call_ready()
        c = CounterNode()
        p.add_child(c)
        assert c.count == 1


class TestNodeProcess:
    def test_process_calls_update(self):
        class UpdatingNode(Node):
            def __init__(self):
                super().__init__("updater")
                self.delta = None

            def _update(self, delta):
                self.delta = delta

        n = UpdatingNode()
        n._process(0.016)
        assert n.delta == pytest.approx(0.016)

    def test_process_skips_invisible(self):
        class UpdatingNode(Node):
            def __init__(self):
                super().__init__("updater")
                self.delta = None

            def _update(self, delta):
                self.delta = delta

        n = UpdatingNode()
        n.visible = False
        n._process(0.016)
        assert n.delta is None

    def test_process_propagates_to_children(self):
        class UpdatingNode(Node):
            def __init__(self):
                super().__init__("updater")
                self.delta = None

            def _update(self, delta):
                self.delta = delta

        p = UpdatingNode()
        c = UpdatingNode()
        p.add_child(c)
        p._process(0.016)
        assert p.delta == pytest.approx(0.016)
        assert c.delta == pytest.approx(0.016)


class TestNodeContainerSugar:
    def test_getitem_by_name(self):
        p = Node("p")
        c = Node("c", parent=p)
        assert p["c"] is c

    def test_getitem_by_index(self):
        p = Node("p")
        c1 = Node("c1", parent=p)
        c2 = Node("c2", parent=p)
        assert p[0] is c1
        assert p[1] is c2

    def test_getitem_missing_raises_keyerror(self):
        p = Node("p")
        with pytest.raises(KeyError):
            _ = p["missing"]

    def test_getitem_bad_type_raises_typeerror(self):
        p = Node("p")
        with pytest.raises(TypeError):
            _ = p[1.5]

    def test_iter_yields_children(self):
        p = Node("p")
        c1 = Node("c1", parent=p)
        c2 = Node("c2", parent=p)
        assert list(p) == [c1, c2]

    def test_len_returns_child_count(self):
        p = Node("p")
        assert len(p) == 0
        Node("c1", parent=p)
        assert len(p) == 1
        Node("c2", parent=p)
        assert len(p) == 2

    def test_contains_child_ref(self):
        p = Node("p")
        c = Node("c", parent=p)
        assert c in p

    def test_contains_missing_child_ref(self):
        p = Node("p")
        c = Node("c")
        assert c not in p

    def test_contains_by_name(self):
        p = Node("p")
        Node("c", parent=p)
        assert "c" in p

    def test_contains_missing_name(self):
        p = Node("p")
        assert "missing" not in p

    def test_iadd_adds_child(self):
        p = Node("p")
        c = Node("c")
        p += c
        assert c.parent is p
        assert c in p.children

    def test_iadd_returns_self(self):
        p = Node("p")
        c = Node("c")
        result = p.__iadd__(c)
        assert result is p

    def test_isub_removes_child(self):
        p = Node("p")
        c = Node("c", parent=p)
        p -= c
        assert c.parent is None
        assert c not in p.children

    def test_isub_returns_self(self):
        p = Node("p")
        c = Node("c", parent=p)
        result = p.__isub__(c)
        assert result is p


class TestNodeQueueFree:
    def setup_method(self):
        Node._deferred_free_queue.clear()

    def test_queue_free_flags_node(self):
        n = Node("n")
        n.queue_free()
        assert n._queued_for_free is True
        assert n in Node._deferred_free_queue

    def test_queue_free_is_idempotent(self):
        n = Node("n")
        n.queue_free()
        n.queue_free()
        assert Node._deferred_free_queue.count(n) == 1

    def test_perform_free_removes_from_parent(self):
        p = Node("p")
        c = Node("c", parent=p)
        c.queue_free()
        c._perform_free()
        assert c.parent is None
        assert c not in p.children

    def test_perform_free_emits_tree_exited(self):
        p = Node("p")
        c = Node("c", parent=p)
        received = []
        c.tree_exited.connect(lambda node: received.append(node.name))
        c.queue_free()
        c._perform_free()
        assert received == ["c"]

    def test_perform_free_frees_children(self):
        p = Node("p")
        c = Node("c", parent=p)
        gc = Node("gc", parent=c)
        c.queue_free()
        c._perform_free()
        assert gc.parent is None
        assert gc not in c.children
        assert c.parent is None
        assert c not in p.children
