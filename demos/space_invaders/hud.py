import tkinter as tk
from Engine.Node import Node
from Engine.Camera2D import Camera2D
class HUD(Node):
    def __init__(self):
        super().__init__("HUD")
        self.score = 0
        self.lives = 3
        self.show_go = False
    def _draw(self, canvas, cam):
        self._canvas_ids.append(
            canvas.create_text(14, 14, anchor="nw", text=f"SCORE: {self.score}", fill="white", font=("Courier", 16, "bold"))
        )
        self._canvas_ids.append(
            canvas.create_text(14, 38, anchor="nw", text=f"LIVES: {self.lives}", fill="white", font=("Courier", 14))
        )
        if self.show_go:
            c = Camera2D._active
            if c:
                cx, cy = c.viewport_w // 2, c.viewport_h // 2
                self._canvas_ids.append(
                    canvas.create_text(cx, cy - 20, text="GAME OVER", fill="red", font=("Courier", 32, "bold"), anchor="center")
                )
                self._canvas_ids.append(
                    canvas.create_text(cx, cy + 20, text="Press ENTER to restart", fill="#aaaaaa", font=("Courier", 14), anchor="center")
                )
