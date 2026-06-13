"""
Engine/Quadtree.py  (now a spatial hash)

Spatial hashing divides the world into a uniform grid. Each shape is inserted
into every grid cell its AABB overlaps. Queries collect all shapes in the
touched cells and deduplicate.

For the object sizes in NodePy (~20–50 px) a 100 px cell gives a good balance
between few cells per shape and tight culling.

Complexity
----------
Insert:  O(1) average per cell, typically 1–4 cells per shape
Query:   O(1 + k) where k is the number of shapes in touched cells
Rebuild: O(n)      called once per frame by GameLoop
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from Engine.CollisionShape import CollisionShape

AABB = Tuple[float, float, float, float]


class SpatialHash:
    """
    Flat grid spatial index. Create one per frame, insert all active shapes,
    then query each shape for its candidates.

    Parameters
    ----------
    cell_size  side length of each square grid cell in world units.
               Default 100 works well for typical 20–50 px sprites.
    """

    def __init__(self, cell_size: float = 100.0):
        self.cell_size: float = cell_size
        self.cells: Dict[Tuple[int, int], List["CollisionShape"]] = {}

    def insert(self, shape: "CollisionShape") -> None:
        """Insert a single CollisionShape into all cells its AABB overlaps."""
        if not shape.visible:
            return
        aabb = shape.get_aabb()
        shape._cached_aabb = aabb  # reused by query/overlaps this frame
        x0, y0, x1, y1 = aabb
        cs = self.cell_size
        cx_min = int(x0 // cs)
        cx_max = int(x1 // cs)
        cy_min = int(y0 // cs)
        cy_max = int(y1 // cs)
        for cx in range(cx_min, cx_max + 1):
            for cy in range(cy_min, cy_max + 1):
                key = (cx, cy)
                if key not in self.cells:
                    self.cells[key] = []
                self.cells[key].append(shape)

    def query(self, aabb: AABB) -> List["CollisionShape"]:
        """Return all shapes whose AABB intersects the given region."""
        x0, y0, x1, y1 = aabb
        cs = self.cell_size
        cx_min = int(x0 // cs)
        cx_max = int(x1 // cs)
        cy_min = int(y0 // cs)
        cy_max = int(y1 // cs)
        seen: Set[int] = set()
        result: List["CollisionShape"] = []
        for cx in range(cx_min, cx_max + 1):
            for cy in range(cy_min, cy_max + 1):
                cell = self.cells.get((cx, cy))
                if cell:
                    for shape in cell:
                        sid = id(shape)
                        if sid not in seen:
                            seen.add(sid)
                            # Narrow-phase AABB check to filter false positives.
                            # _cached_aabb may be None if the shape moved since
                            # the spatial hash was rebuilt (e.g. signal callback).
                            aabb = shape._cached_aabb or shape.get_aabb()
                            sx0, sy0, sx1, sy1 = aabb
                            if sx0 < x1 and sx1 > x0 and sy0 < y1 and sy1 > y0:
                                result.append(shape)
        return result

    def query_shape(self, shape: "CollisionShape") -> List["CollisionShape"]:
        """Convenience: query by a shape's own AABB, excluding itself."""
        candidates = self.query(shape._cached_aabb or shape.get_aabb())
        return [c for c in candidates if c is not shape]

    def debug_draw(self, canvas, cam) -> None:
        """Draw occupied cell boundaries — useful during development."""
        drawn: Set[Tuple[int, int]] = set()
        for key in self.cells:
            if key in drawn or not self.cells[key]:
                continue
            drawn.add(key)
            cx, cy = key
            x0 = cx * self.cell_size
            y0 = cy * self.cell_size
            x1 = x0 + self.cell_size
            y1 = y0 + self.cell_size
            corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            pts = []
            for wx, wy in corners:
                sx, sy = cam.multiply_vec(wx, wy)
                pts.extend([sx, sy])
            canvas.create_polygon(pts, fill="", outline="#444444",
                                  width=1, dash=(2, 4))
