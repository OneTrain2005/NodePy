"""Unit tests for Engine.Input"""

import pytest
from Engine.Input import Input
from Engine.Vector2d import Vector2d


class TestInputActionMap:
    def test_default_actions_exist(self):
        assert "move_left" in Input._action_map
        assert "move_right" in Input._action_map
        assert "jump" in Input._action_map

    def test_add_action(self):
        Input.add_action("custom", ["x", "y"])
        assert Input._action_map["custom"] == ["x", "y"]
        # Clean up
        del Input._action_map["custom"]

    def test_keys_for_returns_action_name_as_fallback(self):
        # An action that doesn't exist falls back to using the name as a key
        keys = Input._keys_for("nonexistent")
        assert keys == ["nonexistent"]


class TestInputKeyState:
    def test_is_action_pressed_true(self):
        Input._held.add("space")
        assert Input.is_action_pressed("jump") is True
        Input._held.discard("space")

    def test_is_action_pressed_false(self):
        Input._held.discard("space")
        assert Input.is_action_pressed("jump") is False

    def test_is_action_just_pressed(self):
        Input._just_pressed.add("Return")
        assert Input.is_action_just_pressed("confirm") is True
        Input._just_pressed.clear()

    def test_is_action_just_released(self):
        Input._just_released.add("Escape")
        assert Input.is_action_just_released("cancel") is True
        Input._just_released.clear()

    def test_is_action_pressed_any_binding(self):
        # move_right binds to both "Right" and "d"
        Input._held.add("d")
        assert Input.is_action_pressed("move_right") is True
        Input._held.discard("d")


class TestInputAxis:
    def test_get_axis_positive(self):
        Input._held.add("Right")
        assert Input.get_axis("move_left", "move_right") == 1.0
        Input._held.discard("Right")

    def test_get_axis_negative(self):
        Input._held.add("Left")
        assert Input.get_axis("move_left", "move_right") == -1.0
        Input._held.discard("Left")

    def test_get_axis_both_pressed_cancels(self):
        Input._held.add("Left")
        Input._held.add("Right")
        assert Input.get_axis("move_left", "move_right") == 0.0
        Input._held.discard("Left")
        Input._held.discard("Right")

    def test_get_axis_none_pressed(self):
        Input._held.discard("Left")
        Input._held.discard("Right")
        assert Input.get_axis("move_left", "move_right") == 0.0


class TestInputVector:
    def test_get_vector_right(self):
        Input._held.add("Right")
        v = Input.get_vector("move_left", "move_right", "move_up", "move_down")
        assert v.x == 1.0
        assert v.y == 0.0
        Input._held.discard("Right")

    def test_get_vector_up_left(self):
        Input._held.add("Left")
        Input._held.add("Up")
        v = Input.get_vector("move_left", "move_right", "move_up", "move_down")
        assert v.x == -1.0
        assert v.y == -1.0
        Input._held.discard("Left")
        Input._held.discard("Up")

    def test_get_vector_zero(self):
        Input._held.clear()
        v = Input.get_vector("move_left", "move_right", "move_up", "move_down")
        assert v.x == 0.0
        assert v.y == 0.0


class TestInputMouse:
    def test_mouse_position_default(self):
        pos = Input.mouse_position()
        assert pos.x == 0.0
        assert pos.y == 0.0

    def test_is_mouse_pressed(self):
        Input._mouse_held.add(1)
        assert Input.is_mouse_pressed(1) is True
        assert Input.is_mouse_pressed(3) is False
        Input._mouse_held.discard(1)

    def test_mouse_just_pressed(self):
        Input._mouse_just_pressed.add(3)
        assert Input.mouse_just_pressed(3) is True
        assert Input.mouse_just_pressed(1) is False
        Input._mouse_just_pressed.clear()

    def test_mouse_just_released(self):
        Input._mouse_just_released.add(2)
        assert Input.mouse_just_released(2) is True
        assert Input.mouse_just_released(1) is False
        Input._mouse_just_released.clear()


class TestInputFlush:
    def test_flush_clears_per_frame_state(self):
        Input._just_pressed.add("space")
        Input._just_released.add("Escape")
        Input._mouse_just_pressed.add(1)
        Input._mouse_just_released.add(3)
        Input._flush()
        assert len(Input._just_pressed) == 0
        assert len(Input._just_released) == 0
        assert len(Input._mouse_just_pressed) == 0
        assert len(Input._mouse_just_released) == 0

    def test_flush_preserves_held_state(self):
        Input._held.add("space")
        Input._flush()
        assert "space" in Input._held
        Input._held.discard("space")


@pytest.fixture(autouse=True)
def reset_input_state():
    """Reset Input state before and after each test."""
    # Save original state
    orig_action_map = dict(Input._action_map)
    orig_held = set(Input._held)
    orig_just_pressed = set(Input._just_pressed)
    orig_just_released = set(Input._just_released)
    orig_mouse_pos = Input._mouse_pos
    orig_mouse_held = set(Input._mouse_held)
    orig_mouse_just_pressed = set(Input._mouse_just_pressed)
    orig_mouse_just_released = set(Input._mouse_just_released)

    # Clear for test
    Input._held.clear()
    Input._just_pressed.clear()
    Input._just_released.clear()
    Input._mouse_pos = Vector2d()
    Input._mouse_held.clear()
    Input._mouse_just_pressed.clear()
    Input._mouse_just_released.clear()

    yield

    # Restore
    Input._action_map.clear()
    Input._action_map.update(orig_action_map)
    Input._held.clear()
    Input._held.update(orig_held)
    Input._just_pressed.clear()
    Input._just_pressed.update(orig_just_pressed)
    Input._just_released.clear()
    Input._just_released.update(orig_just_released)
    Input._mouse_pos = orig_mouse_pos
    Input._mouse_held.clear()
    Input._mouse_held.update(orig_mouse_held)
    Input._mouse_just_pressed.clear()
    Input._mouse_just_pressed.update(orig_mouse_just_pressed)
    Input._mouse_just_released.clear()
    Input._mouse_just_released.update(orig_mouse_just_released)
