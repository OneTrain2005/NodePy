"""Unit tests for Engine.Quadtree (now a spatial hash)"""

import pytest
from Engine.Quadtree import SpatialHash
from Engine.CollisionShape import CollisionShape
from Engine.Node import Node
from Engine.Vector2d import Vector2d


class TestSpatialHashInsert:
    def test_insert_single_shape(self):
        sh = SpatialHash()
        parent = Node("p")
        shape = CollisionShape("s", width=20, height=20, parent=parent)
        sh.insert(shape)
        result = sh.query(shape.get_aabb())
        assert shape in result

    def test_insert_invisible_skipped(self):
        sh = SpatialHash()
        parent = Node("p")
        shape = CollisionShape("s", width=20, height=20, parent=parent)
        shape.visible = False
        sh.insert(shape)
        result = sh.query(shape.get_aabb())
        assert shape not in result

    def test_insert_many_findable(self):
        sh = SpatialHash(cell_size=100.0)
        shapes = []
        for i in range(10):
            p = Node(f"p{i}", relative_pos=Vector2d(i * 30, 0))
            s = CollisionShape(f"s{i}", width=20, height=20, parent=p)
            shapes.append(s)
            sh.insert(s)
        for s in shapes:
            result = sh.query(s.get_aabb())
            assert s in result


class TestSpatialHashQuery:
    def test_query_empty_region(self):
        sh = SpatialHash()
        assert sh.query((1000, 1000, 2000, 2000)) == []

    def test_query_returns_intersecting_shapes(self):
        sh = SpatialHash()
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(100, 0))
        s1 = CollisionShape("s1", width=20, height=20, parent=p1)
        s2 = CollisionShape("s2", width=20, height=20, parent=p2)
        sh.insert(s1)
        sh.insert(s2)
        result = sh.query((-15, -15, 15, 15))
        assert s1 in result
        assert s2 not in result

    def test_query_shape_excludes_self(self):
        sh = SpatialHash()
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(5, 0))
        s1 = CollisionShape("s1", width=20, height=20, parent=p1)
        s2 = CollisionShape("s2", width=20, height=20, parent=p2)
        sh.insert(s1)
        sh.insert(s2)
        result = sh.query_shape(s1)
        assert s1 not in result
        assert s2 in result

    def test_query_returns_no_duplicates(self):
        sh = SpatialHash(cell_size=10.0)
        p = Node("p", relative_pos=Vector2d(0, 0))
        s = CollisionShape("s", width=20, height=20, parent=p)
        sh.insert(s)
        # Query a large region that overlaps the shape across many cells
        result = sh.query((-100, -100, 100, 100))
        assert result.count(s) == 1


class TestSpatialHashCaching:
    def test_insert_caches_aabb(self):
        sh = SpatialHash()
        p = Node("p", relative_pos=Vector2d(10, 20))
        s = CollisionShape("s", width=20, height=20, parent=p)
        assert s._cached_aabb is None
        sh.insert(s)
        assert s._cached_aabb is not None
        assert s._cached_aabb == s.get_aabb()


@pytest.fixture(autouse=True)
def clean_collision_registry():
    """Reset CollisionShape._all before and after each test."""
    original = list(CollisionShape._all)
    CollisionShape._all.clear()
    yield
    CollisionShape._all.clear()
    CollisionShape._all.extend(original)
