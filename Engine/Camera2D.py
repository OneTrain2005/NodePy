from __future__ import annotations
from Engine.Node import Node
from Engine.Matrix3x3 import Matrix3x3
from Engine.Vector2d import Vector2d
from typing import Optional, Tuple

class Camera2D(Node):
    """
    Viewport camera.  The GameLoop uses the *active* camera to build a
    view matrix that is pre-multiplied onto every draw call.

    The view matrix centres the camera's world position on the screen and
    applies zoom around that centre.

    Parameters
    ----------
    viewport_size   (width, height) of the canvas in pixels
    zoom            Uniform scale applied around the camera centre.
                    zoom=2 makes everything appear twice as large.
    offset          Additional screen-space offset (e.g. to aim at the
                    player's feet rather than their centre).
    """

    # The GameLoop reads this to find the current camera
    _active: Optional["Camera2D"] = None

    def __init__(self, name: str = "Camera2D",
                 viewport_size: Tuple[int, int] = (800, 600),
                 zoom: float = 1.0,
                 offset: Optional[Vector2d] = None,
                 parent: Optional[Node] = None):
        super().__init__(name, parent=parent)
        self.viewport_w, self.viewport_h = viewport_size
        self.zoom   = zoom
        self.offset = offset or Vector2d()

    def make_active(self) -> None:
        Camera2D._active = self

    def get_view_matrix(self) -> Matrix3x3:
        """
        Build the camera→screen transform:
            1. Translate world so camera position is at origin
            2. Apply zoom
            3. Translate origin to screen centre
        """
        gpos = self.global_position
        cx   = self.viewport_w / 2 + self.offset.x
        cy   = self.viewport_h / 2 + self.offset.y

        # Move world so camera pos → origin
        T_neg = Matrix3x3.translation(Vector2d(-gpos.x, -gpos.y))
        # Zoom
        Z     = Matrix3x3.scaling(Vector2d(self.zoom, self.zoom))
        # Move origin to screen centre
        T_scr = Matrix3x3.translation(Vector2d(cx, cy))

        return T_scr * Z * T_neg