"""Unit tests for Engine.Camera2D"""

import pytest
from Engine.Camera2D import Camera2D
from Engine.Node import Node
from Engine.Vector2d import Vector2d


class TestCamera2DInit:
    def test_default_init(self):
        cam = Camera2D()
        assert cam.name == "Camera2D"
        assert cam.viewport_w == 800
        assert cam.viewport_h == 600
        assert cam.zoom == 1.0
        assert cam.offset.x == 0.0
        assert cam.offset.y == 0.0

    def test_custom_viewport(self):
        cam = Camera2D(viewport_size=(1024, 768))
        assert cam.viewport_w == 1024
        assert cam.viewport_h == 768

    def test_custom_zoom(self):
        cam = Camera2D(zoom=2.0)
        assert cam.zoom == 2.0

    def test_custom_offset(self):
        cam = Camera2D(offset=Vector2d(10, 20))
        assert cam.offset.x == 10
        assert cam.offset.y == 20


class TestCamera2DActive:
    def test_make_active_sets_class_variable(self):
        cam = Camera2D()
        cam.make_active()
        assert Camera2D._active is cam

    def test_active_can_be_none(self):
        Camera2D._active = None
        assert Camera2D._active is None


class TestCamera2DViewMatrix:
    def test_view_matrix_at_origin_zoom_1(self):
        cam = Camera2D(viewport_size=(800, 600), zoom=1.0)
        cam.make_active()
        mat = cam.get_view_matrix()
        # World origin at (0,0) should map to screen centre (400,300)
        sx, sy = mat.multiply_vec(0, 0)
        assert sx == pytest.approx(400.0)
        assert sy == pytest.approx(300.0)

    def test_view_matrix_with_camera_position(self):
        cam = Camera2D(viewport_size=(800, 600), zoom=1.0)
        cam.relative_pos = Vector2d(100, 50)
        mat = cam.get_view_matrix()
        # Camera at (100,50): world point (100,50) should be at screen centre
        sx, sy = mat.multiply_vec(100, 50)
        assert sx == pytest.approx(400.0)
        assert sy == pytest.approx(300.0)

    def test_view_matrix_with_zoom(self):
        cam = Camera2D(viewport_size=(800, 600), zoom=2.0)
        cam.make_active()
        mat = cam.get_view_matrix()
        # At zoom=2, a point 10 units from camera should be 20 pixels from centre
        sx, sy = mat.multiply_vec(10, 0)
        # centre = 400, plus 10*2 = 20
        assert sx == pytest.approx(420.0)
        assert sy == pytest.approx(300.0)

    def test_view_matrix_with_offset(self):
        cam = Camera2D(viewport_size=(800, 600), zoom=1.0, offset=Vector2d(50, -30))
        mat = cam.get_view_matrix()
        sx, sy = mat.multiply_vec(0, 0)
        # Centre (400,300) + offset (50,-30) = (450, 270)
        assert sx == pytest.approx(450.0)
        assert sy == pytest.approx(270.0)

    def test_view_matrix_combined(self):
        cam = Camera2D(viewport_size=(800, 600), zoom=2.0, offset=Vector2d(10, 10))
        cam.relative_pos = Vector2d(100, 100)
        mat = cam.get_view_matrix()
        # World point at camera position should land at centre + offset
        sx, sy = mat.multiply_vec(100, 100)
        assert sx == pytest.approx(410.0)
        assert sy == pytest.approx(310.0)
