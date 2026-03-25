from __future__ import annotations
import tkinter as tk
import time
from Vector2d import Vector2d
from Node import Node

class MatrixVisualizer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Scene graph demo")
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="#222")
        self.canvas.pack()

        # Build hierarchy
        self.origin = Node("Center", Vector2d(400, 300))

        # A long, stretched "Arm"
        self.arm = Node("Arm", Vector2d(100, 0), self.origin)
        self.arm.scale = Vector2d(4.0, 0.5)   # long and thin
        self.arm.rotation = 45

        # A "Hand" at the end of the arm.
        # NOTE: relative_pos is in the ARM's local space (before arm's own
        # scale/rotation), so (40, 0) means 40 units along the arm's local X.
        # The fixed TRS order makes this behave predictably.
        self.hand = Node("Hand", Vector2d(40, 0), self.arm)
        self.hand.scale = Vector2d(0.5, 2.0)  # tall and thin

        self._last_time = time.perf_counter()
        self.animate()
        self.root.mainloop()

    # ---- Node colors are now determined by the node itself, not the caller

    NODE_COLORS = {
        "Center": "yellow",
        "Arm":    "orange",
        "Hand":   "cyan",
    }
    DEFAULT_COLOR = "white"

    def draw_node_box(self, node: Node):
        mat = node.global_matrix
        color = self.NODE_COLORS.get(node.name, self.DEFAULT_COLOR)

        # Standard 20×20 unit box in local space
        corners = [(-10, -10), (10, -10), (10, 10), (-10, 10)]
        pts = []
        for px, py in corners:
            gx, gy = mat.multiply_vec(px, py)
            pts.extend([gx, gy])

        self.canvas.create_polygon(pts, fill=color, outline="white", width=1)

        # Label below the node origin
        ox, oy = mat.multiply_vec(0, 0)
        self.canvas.create_text(ox, oy + 18, text=node.name, fill="white",
                                font=("Helvetica", 9))

        # Recurse — each child picks its own color
        for child in node.children:
            self.draw_node_box(child)

    def animate(self):
        now = time.perf_counter()
        delta = now - self._last_time  # seconds since last frame
        self._last_time = now

        self.canvas.delete("all")

        # Drive rotations with delta time so speed is frame-rate independent.
        # Units: degrees per second.
        self.origin.rotation = self.origin.rotation + 30 * delta
        self.arm.rotation    = self.arm.rotation    + 60 * delta
        self.hand.rotation   = self.hand.rotation   - 120 * delta

        self.draw_node_box(self.origin)

        # Target ~60 fps; schedule next frame relative to the START of this one
        # to avoid drift from draw time.
        elapsed_ms = int((time.perf_counter() - now) * 1000)
        delay = max(1, 16 - elapsed_ms)
        self.root.after(delay, self.animate)


if __name__ == "__main__":
    MatrixVisualizer()