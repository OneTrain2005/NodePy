"""Unit tests for Engine.Vector2d"""

import math
import pytest
from Engine.Vector2d import Vector2d


class TestVector2dInit:
    def test_default_init(self):
        v = Vector2d()
        assert v.x == 0.0
        assert v.y == 0.0

    def test_init_with_values(self):
        v = Vector2d(3.5, -2.0)
        assert v.x == 3.5
        assert v.y == -2.0


class TestVector2dArithmetic:
    def test_add(self):
        a = Vector2d(1, 2)
        b = Vector2d(3, 4)
        c = a + b
        assert c.x == 4
        assert c.y == 6

    def test_add_does_not_mutate_operands(self):
        a = Vector2d(1, 2)
        b = Vector2d(3, 4)
        _ = a + b
        assert a.x == 1 and a.y == 2
        assert b.x == 3 and b.y == 4

    def test_sub(self):
        a = Vector2d(5, 7)
        b = Vector2d(2, 3)
        c = a - b
        assert c.x == 3
        assert c.y == 4

    def test_mul_scalar(self):
        v = Vector2d(2, 3)
        c = v * 4
        assert c.x == 8
        assert c.y == 12

    def test_mul_negative_scalar(self):
        v = Vector2d(2, -3)
        c = v * -2
        assert c.x == -4
        assert c.y == 6


class TestVector2dLength:
    def test_length_zero(self):
        assert Vector2d(0, 0).length() == 0.0

    def test_length_positive(self):
        assert Vector2d(3, 4).length() == 5.0

    def test_length_negative_components(self):
        assert Vector2d(-3, -4).length() == 5.0


class TestVector2dNormalized:
    def test_normalized_unit_vector(self):
        v = Vector2d(1, 0).normalized()
        assert v.x == pytest.approx(1.0)
        assert v.y == pytest.approx(0.0)

    def test_normalized_non_unit(self):
        v = Vector2d(3, 4).normalized()
        assert v.x == pytest.approx(0.6)
        assert v.y == pytest.approx(0.8)

    def test_normalized_zero_vector_returns_zero(self):
        v = Vector2d(0, 0).normalized()
        assert v.x == 0.0
        assert v.y == 0.0


class TestVector2dDot:
    def test_dot_orthogonal(self):
        a = Vector2d(1, 0)
        b = Vector2d(0, 1)
        assert a.dot(b) == 0.0

    def test_dot_parallel(self):
        a = Vector2d(2, 0)
        b = Vector2d(3, 0)
        assert a.dot(b) == 6.0

    def test_dot_negative(self):
        a = Vector2d(1, 0)
        b = Vector2d(-1, 0)
        assert a.dot(b) == -1.0


class TestVector2dDirectionTo:
    def test_direction_to_right(self):
        a = Vector2d(0, 0)
        b = Vector2d(10, 0)
        d = a.direction_to(b)
        assert d.x == pytest.approx(1.0)
        assert d.y == pytest.approx(0.0)

    def test_direction_to_diagonal(self):
        a = Vector2d(0, 0)
        b = Vector2d(1, 1)
        d = a.direction_to(b)
        assert d.x == pytest.approx(math.sqrt(2) / 2)
        assert d.y == pytest.approx(math.sqrt(2) / 2)


class TestVector2dDistanceTo:
    def test_distance_to_same_point(self):
        a = Vector2d(5, 5)
        assert a.distance_to(Vector2d(5, 5)) == 0.0

    def test_distance_to_different_point(self):
        a = Vector2d(0, 0)
        b = Vector2d(3, 4)
        assert a.distance_to(b) == 5.0


class TestVector2dDistanceSquaredTo:
    def test_distance_squared(self):
        a = Vector2d(1, 2)
        b = Vector2d(4, 6)
        assert a.distance_squared_to(b) == 25.0

    def test_distance_squared_avoids_sqrt(self):
        """Make sure we are actually using squared distance (no sqrt in impl)."""
        a = Vector2d(0, 0)
        b = Vector2d(3, 4)
        # 3-4-5 triangle: squared distance should be 25
        assert a.distance_squared_to(b) == 25.0


class TestVector2dEq:
    def test_eq_same_values(self):
        assert Vector2d(3, 4) == Vector2d(3, 4)

    def test_eq_self(self):
        v = Vector2d(1, 2)
        assert v == v

    def test_eq_near_match_with_isclose(self):
        a = Vector2d(1.0, 2.0)
        b = Vector2d(1.0 + 1e-10, 2.0 - 1e-10)
        assert a == b

    def test_eq_different_x(self):
        assert Vector2d(1, 2) != Vector2d(999, 2)

    def test_eq_different_y(self):
        assert Vector2d(1, 2) != Vector2d(1, 999)

    def test_eq_different_both(self):
        assert Vector2d(1, 2) != Vector2d(3, 4)

    def test_eq_zero_vs_zero(self):
        assert Vector2d(0, 0) == Vector2d(0, 0)

    def test_eq_against_non_vector_returns_false(self):
        assert Vector2d(1, 2) != "not a vector"
        assert Vector2d(1, 2) != None
        assert Vector2d(1, 2) != (1, 2)

    def test_eq_large_values(self):
        assert Vector2d(1e9, 1e9) == Vector2d(1e9, 1e9)

    def test_eq_negative_values(self):
        assert Vector2d(-5, -10) == Vector2d(-5, -10)

    def test_eq_symmetric(self):
        a = Vector2d(2.5, 3.5)
        b = Vector2d(2.5, 3.5)
        assert (a == b) == (b == a)


class TestVector2dRepr:
    def test_repr_format(self):
        v = Vector2d(1.5, 2.75)
        assert repr(v) == "Vector2d(1.50, 2.75)"
