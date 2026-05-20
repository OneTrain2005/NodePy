"""Unit tests for Engine.Quadtree"""

import pytest
from Engine.Quadtree import Quadtree, _QTNode, _aabb_intersects, _aabb_fits_inside
from Engine.CollisionShape import CollisionShape
from Engine.Node import Node
from Engine.Vector2d import Vector2d


class TestAABBHelpers:
    def test_aabb_intersects_overlapping(self):
        a = (0, 0, 10, 10)
        b = (5, 5, 15, 15)
        assert _aabb_intersects(a, b) is True

    def test_aabb_intersects_disjoint(self):
        a = (0, 0, 10, 10)
        b = (20, 20, 30, 30)
        assert _aabb_intersects(a, b) is False

    def test_aabb_intersects_touching_edge(self):
        # Touching at edge: a[2] == b[0], so a[2] > b[0] is False
        a = (0, 0, 10, 10)
        b = (10, 0, 20, 10)
        assert _aabb_intersects(a, b) is False

    def test_aabb_fits_inside_true(self):
        outer = (0, 0, 20, 20)
        inner = (5, 5, 15, 15)
        assert _aabb_fits_inside(inner, outer) is True

    def test_aabb_fits_inside_false(self):
        outer = (0, 0, 10, 10)
        inner = (5, 5, 15, 15)
        assert _aabb_fits_inside(inner, outer) is False

    def test_aabb_fits_inside_equal(self):
        a = (0, 0, 10, 10)
        assert _aabb_fits_inside(a, a) is True


class TestQTNode:
    def test_node_init(self):
        node = _QTNode((0, 0, 100, 100), depth=0)
        assert node.bounds == (0, 0, 100, 100)
        assert node.depth == 0
        assert node.shapes == []
        assert node.children == []

    def test_split_creates_four_children(self):
        node = _QTNode((0, 0, 100, 100))
        node._split()
        assert len(node.children) == 4
        # NW
        assert node.children[0].bounds == (0, 0, 50, 50)
        # NE
        assert node.children[1].bounds == (50, 0, 100, 50)
        # SW
        assert node.children[2].bounds == (0, 50, 50, 100)
        # SE
        assert node.children[3].bounds == (50, 50, 100, 100)

    def test_quadrant_for_fits(self):
        node = _QTNode((0, 0, 100, 100))
        node._split()
        child = node._quadrant_for((60, 10, 90, 40))
        assert child is node.children[1]  # NE

    def test_quadrant_for_straddler_returns_none(self):
        node = _QTNode((0, 0, 100, 100))
        node._split()
        child = node._quadrant_for((40, 40, 60, 60))
        assert child is None


class TestQuadtreeInsert:
    def test_insert_single_shape(self):
        qt = Quadtree()
        parent = Node("p")
        shape = CollisionShape("s", width=20, height=20, parent=parent)
        qt.insert(shape)
        # Shape should be findable by querying its own AABB
        result = qt.query(shape.get_aabb())
        assert shape in result

    def test_insert_invisible_skipped(self):
        qt = Quadtree()
        parent = Node("p")
        shape = CollisionShape("s", width=20, height=20, parent=parent)
        shape.visible = False
        qt.insert(shape)
        result = qt.query(shape.get_aabb())
        assert shape not in result

    def test_insert_many_triggers_split(self):
        qt = Quadtree(bounds=(-1000, -1000, 1000, 1000))
        shapes = []
        for i in range(10):
            p = Node(f"p{i}", relative_pos=Vector2d(i * 30, 0))
            s = CollisionShape(f"s{i}", width=20, height=20, parent=p)
            shapes.append(s)
            qt.insert(s)
        # All shapes should still be findable
        for s in shapes:
            result = qt.query(s.get_aabb())
            assert s in result


class TestQuadtreeQuery:
    def test_query_empty_region(self):
        qt = Quadtree()
        assert qt.query((1000, 1000, 2000, 2000)) == []

    def test_query_returns_intersecting_shapes(self):
        qt = Quadtree()
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(100, 0))
        s1 = CollisionShape("s1", width=20, height=20, parent=p1)
        s2 = CollisionShape("s2", width=20, height=20, parent=p2)
        qt.insert(s1)
        qt.insert(s2)
        result = qt.query((-15, -15, 15, 15))
        assert s1 in result
        assert s2 not in result

    def test_query_shape_excludes_self(self):
        qt = Quadtree()
        p1 = Node("p1", relative_pos=Vector2d(0, 0))
        p2 = Node("p2", relative_pos=Vector2d(5, 0))
        s1 = CollisionShape("s1", width=20, height=20, parent=p1)
        s2 = CollisionShape("s2", width=20, height=20, parent=p2)
        qt.insert(s1)
        qt.insert(s2)
        result = qt.query_shape(s1)
        assert s1 not in result
        assert s2 in result

    def test_query_returns_no_duplicates(self):
        qt = Quadtree()
        p = Node("p", relative_pos=Vector2d(0, 0))
        s = CollisionShape("s", width=20, height=20, parent=p)
        qt.insert(s)
        # Query a large region that overlaps the shape multiple times
        result = qt.query((-100, -100, 100, 100))
        assert result.count(s) == 1


class TestQuadtreeCaching:
    def test_insert_caches_aabb(self):
        qt = Quadtree()
        p = Node("p", relative_pos=Vector2d(10, 20))
        s = CollisionShape("s", width=20, height=20, parent=p)
        assert s._cached_aabb is None
        qt.insert(s)
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
