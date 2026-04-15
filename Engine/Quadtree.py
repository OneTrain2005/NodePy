"""
Engine/Quadtree.py

Spatial partitioning via a quadtree.  Rebuilt from scratch every frame by
GameLoop, then queried by CollisionShape._update instead of scanning _all.

How it works
------------
The world is divided into four quadrants recursively.  Each node holds up to
MAX_OBJECTS shapes before splitting into four children.  A shape that straddles
a boundary is kept in the parent node (the "straddler" rule) so it is never
double-counted.

Complexity
----------
Insert:  O(log n) average
Query:   O(log n + k)  where k = shapes in the same region
Rebuild: O(n log n)    called once per frame by GameLoop

Usage (handled automatically by GameLoop + CollisionShape)
----------------------------------------------------------
    qt = Quadtree(bounds=(-2000, -2000, 2000, 2000))
    for shape in CollisionShape._all:
        qt.insert(shape)
    candidates = qt.query(my_shape.get_aabb())
"""

from __future__ import annotations
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from Engine.CollisionShape import CollisionShape

# (min_x, min_y, max_x, max_y)
AABB = Tuple[float, float, float, float]

MAX_OBJECTS = 6   # shapes per node before splitting
MAX_DEPTH   = 8   # never subdivide beyond this level


def _aabb_intersects(a: AABB, b: AABB) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def _aabb_fits_inside(inner: AABB, outer: AABB) -> bool:
    """True if inner is fully contained within outer."""
    return (inner[0] >= outer[0] and inner[2] <= outer[2]
            and inner[1] >= outer[1] and inner[3] <= outer[3])


class _QTNode:
    """A single node (region) in the quadtree."""

    __slots__ = ("bounds", "depth", "shapes", "children")

    def __init__(self, bounds: AABB, depth: int = 0):
        self.bounds:   AABB                     = bounds
        self.depth:    int                      = depth
        self.shapes:   List["CollisionShape"]   = []
        self.children: List["_QTNode"]          = []   # empty = leaf

    # ── Subdivision ──────────────────────────────────────────────────────────

    def _split(self) -> None:
        x0, y0, x1, y1 = self.bounds
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        d = self.depth + 1
        self.children = [
            _QTNode((x0, y0, mx, my), d),   # NW
            _QTNode((mx, y0, x1, my), d),   # NE
            _QTNode((x0, my, mx, y1), d),   # SW
            _QTNode((mx, my, x1, y1), d),   # SE
        ]

    def _quadrant_for(self, aabb: AABB) -> "_QTNode | None":
        """Return the child quadrant that fully contains aabb, or None."""
        for child in self.children:
            if _aabb_fits_inside(aabb, child.bounds):
                return child
        return None

    # ── Insert ───────────────────────────────────────────────────────────────

    def insert(self, shape: "CollisionShape", aabb: AABB) -> None:
        # If we have children, try to push the shape down
        if self.children:
            target = self._quadrant_for(aabb)
            if target is not None:
                target.insert(shape, aabb)
                return
            # Straddles a boundary — keep at this level
            self.shapes.append(shape)
            return

        # Leaf node
        self.shapes.append(shape)

        # Split if over capacity and not at max depth
        if len(self.shapes) > MAX_OBJECTS and self.depth < MAX_DEPTH:
            self._split()
            # Re-distribute existing shapes into children where possible
            remaining = []
            for s in self.shapes:
                s_aabb = s._cached_aabb
                target = self._quadrant_for(s_aabb)
                if target is not None:
                    target.insert(s, s_aabb)
                else:
                    remaining.append(s)
            self.shapes = remaining

    # ── Query ────────────────────────────────────────────────────────────────

    def query(self, aabb: AABB, result: List["CollisionShape"]) -> None:
        """
        Append every shape whose AABB intersects `aabb` into result.
        Walks only the branches that overlap with the query region.
        """
        # Shapes stored at this node always need to be checked (straddlers
        # and leaf contents both live here)
        for shape in self.shapes:
            if _aabb_intersects(shape._cached_aabb, aabb):
                result.append(shape)

        # Recurse into children that overlap the query region
        for child in self.children:
            if _aabb_intersects(child.bounds, aabb):
                child.query(aabb, result)


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

class Quadtree:
    """
    Top-level quadtree.  Create one per frame, insert all active shapes,
    then query each shape for its candidates.

    Parameters
    ----------
    bounds  (min_x, min_y, max_x, max_y) in world space.
            Shapes outside this region are still inserted at the root —
            they are never silently dropped.
    """

    def __init__(self, bounds: AABB = (-4000, -4000, 4000, 4000)):
        self._root = _QTNode(bounds, depth=0)

    def insert(self, shape: "CollisionShape") -> None:
        """Insert a single CollisionShape into the tree."""
        if not shape.visible:
            return
        aabb = shape.get_aabb()
        shape._cached_aabb = aabb   # reused by query/overlaps this frame
        self._root.insert(shape, aabb)

    def query(self, aabb: AABB) -> List["CollisionShape"]:
        """Return all shapes whose AABB intersects the given region."""
        result: List["CollisionShape"] = []
        self._root.query(aabb, result)
        return result

    def query_shape(self, shape: "CollisionShape") -> List["CollisionShape"]:
        """Convenience: query by a shape's own AABB, excluding itself."""
        candidates = self.query(shape._cached_aabb or shape.get_aabb())
        return [c for c in candidates if c is not shape]

    def debug_draw(self, canvas, cam) -> None:
        """Draw quadtree cell boundaries — useful during development."""
        self._draw_node(self._root, canvas, cam)

    def _draw_node(self, node: _QTNode, canvas, cam) -> None:
        x0, y0, x1, y1 = node.bounds
        # Transform the four corners through the camera matrix
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pts = []
        for wx, wy in corners:
            sx, sy = cam.multiply_vec(wx, wy)
            pts.extend([sx, sy])
        # Fade colour by depth so deeper cells are dimmer
        alpha = max(20, 80 - node.depth * 12)
        hex_col = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
        canvas.create_polygon(pts, fill="", outline=hex_col,
                              width=1, dash=(2, 4))
        for child in node.children:
            self._draw_node(child, canvas, cam)
