"""Unit tests for Engine.CollisionShape"""

import pytest
from Engine.CollisionShape import CollisionShape
from Engine.Node import Node
from Engine.Vector2d import Vector2d


class TestCollisionShapeInit:
    def test_default_size(self):
        # Need a parent because CollisionShape registers itself in _all
        parent = Node("parent")
        cs = CollisionShape("cs", parent=parent)
        assert cs.width == 20
        assert cs.height == 20
        assert cs.debug_draw is False

    def test_custom_size(self):
        parent = Node("parent")
        cs = CollisionShape("cs", width=50, height=30, parent=parent)
        assert cs.width == 50
        assert cs.height == 30

    def test_registered_in_all(self):
        before = len(CollisionShape._all)
        parent = Node("parent")
        cs = CollisionShape("cs", parent=parent)
        assert cs in CollisionShape._all
        assert len(CollisionShape._all) == before + 1


class TestCollisionShapeAABB:
    def test_aabb_at_origin(self):
        parent = Node("parent")
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        x0, y0, x1, y1 = cs.get_aabb()
        assert x0 == pytest.approx(-10.0)
        assert y0 == pytest.approx(-10.0)
        assert x1 == pytest.approx(10.0)
        assert y1 == pytest.approx(10.0)

    def test_aabb_with_translation(self):
        parent = Node("parent", relative_pos=Vector2d(100, 50))
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        x0, y0, x1, y1 = cs.get_aabb()
        assert x0 == pytest.approx(90.0)
        assert y0 == pytest.approx(40.0)
        assert x1 == pytest.approx(110.0)
        assert y1 == pytest.approx(60.0)

    def test_aabb_with_scale(self):
        parent = Node("parent")
        parent.scale = Vector2d(2, 2)
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        x0, y0, x1, y1 = cs.get_aabb()
        assert x0 == pytest.approx(-20.0)
        assert y0 == pytest.approx(-20.0)
        assert x1 == pytest.approx(20.0)
        assert y1 == pytest.approx(20.0)

    def test_aabb_with_rotation_45(self):
        parent = Node("parent")
        parent.rotation = 45
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        x0, y0, x1, y1 = cs.get_aabb()
        # A 20x20 square rotated 45° has a bounding box of ~28.28 x ~28.28
        expected = 20 * 1.41421356
        assert x1 - x0 == pytest.approx(expected, abs=1e-6)
        assert y1 - y0 == pytest.approx(expected, abs=1e-6)


class TestCollisionShapeOverlaps:
    def test_overlaps_true(self):
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(5, 0))
        cs1 = CollisionShape("cs1", width=20, height=20, parent=p1)
        cs2 = CollisionShape("cs2", width=20, height=20, parent=p2)
        assert cs1.overlaps(cs2) is True

    def test_overlaps_false(self):
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(100, 0))
        cs1 = CollisionShape("cs1", width=20, height=20, parent=p1)
        cs2 = CollisionShape("cs2", width=20, height=20, parent=p2)
        assert cs1.overlaps(cs2) is False

    def test_overlaps_touching_edge_false(self):
        # Edge-touching is not overlapping for AABB with < and >
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(20, 0))
        cs1 = CollisionShape("cs1", width=20, height=20, parent=p1)
        cs2 = CollisionShape("cs2", width=20, height=20, parent=p2)
        # cs1 spans [-10,10], cs2 spans [10,30]; they touch at 10
        assert cs1.overlaps(cs2) is False

    def test_overlaps_uses_cached_aabb(self):
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(5, 0))
        cs1 = CollisionShape("cs1", width=20, height=20, parent=p1)
        cs2 = CollisionShape("cs2", width=20, height=20, parent=p2)
        cs1._cached_aabb = cs1.get_aabb()
        cs2._cached_aabb = cs2.get_aabb()
        assert cs1.overlaps(cs2) is True


class TestCollisionShapeContainsPoint:
    def test_contains_center(self):
        parent = Node("parent", relative_pos=Vector2d(100, 100))
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        assert cs.contains_point(Vector2d(100, 100)) is True

    def test_contains_corner(self):
        parent = Node("parent", relative_pos=Vector2d(0, 0))
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        assert cs.contains_point(Vector2d(10, 10)) is True

    def test_does_not_contain_outside(self):
        parent = Node("parent", relative_pos=Vector2d(0, 0))
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        assert cs.contains_point(Vector2d(100, 100)) is False

    def test_contains_on_edge(self):
        parent = Node("parent", relative_pos=Vector2d(0, 0))
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        # Edge is inclusive
        assert cs.contains_point(Vector2d(10, 0)) is True


class TestCollisionShapeContains:
    def test_contains_point(self):
        parent = Node("parent", relative_pos=Vector2d(0, 0))
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        assert Vector2d(0, 0) in cs

    def test_does_not_contain_point(self):
        parent = Node("parent", relative_pos=Vector2d(0, 0))
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        assert Vector2d(100, 100) not in cs

    def test_contains_non_vector_returns_false(self):
        parent = Node("parent")
        cs = CollisionShape("cs", width=20, height=20, parent=parent)
        assert "string" not in cs
        assert 42 not in cs


class TestCollisionShapeSignals:
    def test_body_entered_exists(self):
        parent = Node("parent")
        cs = CollisionShape("cs", parent=parent)
        assert cs.body_entered.name == "body_entered"

    def test_body_exited_exists(self):
        parent = Node("parent")
        cs = CollisionShape("cs", parent=parent)
        assert cs.body_exited.name == "body_exited"


@pytest.fixture(autouse=True)
def clean_collision_registry():
    """Reset CollisionShape._all before and after each test."""
    original = list(CollisionShape._all)
    CollisionShape._all.clear()
    yield
    CollisionShape._all.clear()
    CollisionShape._all.extend(original)
