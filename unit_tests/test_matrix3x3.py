"""Unit tests for Engine.Matrix3x3"""

import math
import pytest
from Engine.Matrix3x3 import Matrix3x3
from Engine.Vector2d import Vector2d


class TestMatrix3x3Identity:
    def test_default_is_identity(self):
        m = Matrix3x3()
        assert m.m == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    def test_identity_multiply_vec(self):
        m = Matrix3x3()
        assert m.multiply_vec(5, 7) == (5, 7)

    def test_identity_times_identity(self):
        m = Matrix3x3()
        assert (m * m).m == m.m


class TestMatrix3x3Translation:
    def test_translation_multiply_vec(self):
        t = Matrix3x3.translation(Vector2d(10, 20))
        assert t.multiply_vec(3, 4) == (13, 24)

    def test_translation_zero(self):
        t = Matrix3x3.translation(Vector2d(0, 0))
        assert t.multiply_vec(5, 5) == (5, 5)


class TestMatrix3x3Rotation:
    def test_rotation_0_degrees(self):
        r = Matrix3x3.rotation(0)
        assert r.multiply_vec(1, 0) == pytest.approx((1, 0), abs=1e-9)

    def test_rotation_90_degrees_clockwise(self):
        # In screen space, +y is down, so 90° clockwise sends (1,0) to (0,1)
        r = Matrix3x3.rotation(90)
        x, y = r.multiply_vec(1, 0)
        assert x == pytest.approx(0.0, abs=1e-9)
        assert y == pytest.approx(1.0, abs=1e-9)

    def test_rotation_180_degrees(self):
        r = Matrix3x3.rotation(180)
        x, y = r.multiply_vec(1, 0)
        assert x == pytest.approx(-1.0, abs=1e-9)
        assert y == pytest.approx(0.0, abs=1e-9)

    def test_rotation_360_degrees_is_identity(self):
        r = Matrix3x3.rotation(360)
        x, y = r.multiply_vec(3, 4)
        assert x == pytest.approx(3.0, abs=1e-9)
        assert y == pytest.approx(4.0, abs=1e-9)


class TestMatrix3x3Scaling:
    def test_uniform_scale(self):
        s = Matrix3x3.scaling(Vector2d(2, 2))
        assert s.multiply_vec(3, 4) == (6, 8)

    def test_non_uniform_scale(self):
        s = Matrix3x3.scaling(Vector2d(2, 3))
        assert s.multiply_vec(1, 1) == (2, 3)


class TestMatrix3x3Multiplication:
    def test_translation_then_rotation(self):
        t = Matrix3x3.translation(Vector2d(1, 0))
        r = Matrix3x3.rotation(90)
        combined = t * r
        # First rotate (1,0) -> (0,1), then translate by (1,0) -> (1,1)
        assert combined.multiply_vec(1, 0) == pytest.approx((1.0, 1.0), abs=1e-9)

    def test_associative_property(self):
        a = Matrix3x3.rotation(30)
        b = Matrix3x3.scaling(Vector2d(2, 3))
        c = Matrix3x3.translation(Vector2d(10, -5))
        left = (a * b) * c
        right = a * (b * c)
        for i in range(3):
            for j in range(3):
                assert left.m[i][j] == pytest.approx(right.m[i][j], abs=1e-9)


class TestMatrix3x3MakeTransform:
    def test_make_transform_equivalent_to_trs(self):
        pos = Vector2d(10, 20)
        angle = 45
        scale = Vector2d(2, 2)
        trs = Matrix3x3.translation(pos) * Matrix3x3.rotation(angle) * Matrix3x3.scaling(scale)
        direct = Matrix3x3.make_transform(pos, angle, scale)
        for i in range(3):
            for j in range(3):
                assert trs.m[i][j] == pytest.approx(direct.m[i][j], abs=1e-9)

    def test_make_transform_zero_angle(self):
        m = Matrix3x3.make_transform(Vector2d(5, 5), 0, Vector2d(1, 1))
        assert m.multiply_vec(1, 0) == (6, 5)


class TestMatrix3x3InverseTranslate:
    def test_inverse_translate_negates_tx_ty(self):
        m = Matrix3x3.translation(Vector2d(5, 10))
        inv = m.inverse_translate()
        assert inv.m[0][2] == -5
        assert inv.m[1][2] == -10

    def test_inverse_translate_preserves_rotation_scale(self):
        trs = Matrix3x3.make_transform(Vector2d(5, 5), 30, Vector2d(2, 2))
        inv = trs.inverse_translate()
        assert inv.m[0][0] == trs.m[0][0]
        assert inv.m[0][1] == trs.m[0][1]
        assert inv.m[1][0] == trs.m[1][0]
        assert inv.m[1][1] == trs.m[1][1]


class TestMatrix3x3Decompose:
    def test_decompose_translation(self):
        m = Matrix3x3.translation(Vector2d(100, 200))
        tx, ty, rot, sx, sy = m.decompose()
        assert tx == pytest.approx(100.0)
        assert ty == pytest.approx(200.0)
        assert rot == pytest.approx(0.0)
        assert sx == pytest.approx(1.0)
        assert sy == pytest.approx(1.0)

    def test_decompose_rotation(self):
        m = Matrix3x3.rotation(45)
        tx, ty, rot, sx, sy = m.decompose()
        assert tx == pytest.approx(0.0)
        assert ty == pytest.approx(0.0)
        assert rot == pytest.approx(45.0)
        assert sx == pytest.approx(1.0)
        assert sy == pytest.approx(1.0)

    def test_decompose_scale(self):
        m = Matrix3x3.scaling(Vector2d(3, 2))
        tx, ty, rot, sx, sy = m.decompose()
        assert tx == pytest.approx(0.0)
        assert ty == pytest.approx(0.0)
        assert rot == pytest.approx(0.0)
        assert sx == pytest.approx(3.0)
        assert sy == pytest.approx(2.0)

    def test_decompose_trs(self):
        pos = Vector2d(50, -30)
        angle = 60
        scale = Vector2d(2, 0.5)
        m = Matrix3x3.make_transform(pos, angle, scale)
        tx, ty, rot, sx, sy = m.decompose()
        assert tx == pytest.approx(50.0)
        assert ty == pytest.approx(-30.0)
        assert rot == pytest.approx(60.0)
        assert sx == pytest.approx(2.0)
        assert sy == pytest.approx(0.5)
