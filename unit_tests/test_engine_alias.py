"""Unit tests for the deprecated Engine alias of nodepy"""

import importlib
import sys
import warnings

import nodepy


def _import_engine():
    sys.modules.pop("Engine", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        engine = importlib.import_module("Engine")
    return engine, caught


class TestEngineAlias:
    def test_import_warns_deprecated(self):
        _, caught = _import_engine()
        assert any(issubclass(w.category, DeprecationWarning) for w in caught)

    def test_legacy_from_import_returns_same_class(self):
        _import_engine()
        from Engine.Node import Node as LegacyNode
        from nodepy.Node import Node
        assert LegacyNode is Node

    def test_legacy_submodule_is_same_module(self):
        engine, _ = _import_engine()
        import nodepy.Camera2D
        assert sys.modules["Engine.Camera2D"] is sys.modules["nodepy.Camera2D"]
        assert engine.Camera2D is sys.modules["nodepy.Camera2D"]

    def test_class_state_is_shared(self):
        _import_engine()
        from Engine.Camera2D import Camera2D as LegacyCamera
        from nodepy.Camera2D import Camera2D
        old = Camera2D._active
        try:
            LegacyCamera._active = "sentinel"
            assert Camera2D._active == "sentinel"
        finally:
            Camera2D._active = old

    def test_version_matches(self):
        engine, _ = _import_engine()
        assert engine.__version__ == nodepy.__version__


class TestPublicApi:
    def test_root_exports(self):
        from nodepy.Node import Node
        from nodepy.Plugin import Plugin
        assert nodepy.Node is Node
        assert nodepy.Plugin is Plugin
        for name in nodepy.__all__:
            assert hasattr(nodepy, name)
