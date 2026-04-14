import tkinter as tk
from typing import Callable, Optional, Tuple


class RegionSelector:
    """
    Ventana Toplevel de pantalla completa semitransparente para que el
    usuario seleccione la región a traducir arrastrando el mouse.
    Usa wait_window() en lugar de mainloop() para ser modal sin crear
    un intérprete Tcl adicional.
    """

    def __init__(self, root: tk.Tk, callback: Callable[[Tuple[int, int, int, int]], None]):
        self._root = root
        self.callback = callback
        self._start_x = 0
        self._start_y = 0
        self._rect: Optional[int] = None
        self._selected = False

    def start(self):
        self.window = tk.Toplevel(self._root)
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-alpha", 0.35)
        self.window.attributes("-topmost", True)
        self.window.overrideredirect(True)
        self.window.config(bg="black")

        self.canvas = tk.Canvas(
            self.window, cursor="cross", bg="black", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        tk.Label(
            self.canvas,
            text="Haz clic y arrastra para seleccionar la región a traducir  |  ESC para cancelar",
            fg="white",
            bg="black",
            font=("Arial", 13),
        ).place(relx=0.5, rely=0.04, anchor="center")

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.window.bind("<Escape>", lambda _: self.window.destroy())

        # Modal: bloquea hasta que la ventana se cierre, pero sigue
        # procesando eventos del root principal (a diferencia de mainloop())
        self._root.wait_window(self.window)

    def _on_press(self, event: tk.Event):
        self._start_x = event.x
        self._start_y = event.y
        if self._rect:
            self.canvas.delete(self._rect)

    def _on_drag(self, event: tk.Event):
        if self._rect:
            self.canvas.delete(self._rect)
        self._rect = self.canvas.create_rectangle(
            self._start_x, self._start_y, event.x, event.y,
            outline="#00e5ff", width=2, fill="#00e5ff", stipple="gray25",
        )

    def _on_release(self, event: tk.Event):
        x1 = min(self._start_x, event.x)
        y1 = min(self._start_y, event.y)
        x2 = max(self._start_x, event.x)
        y2 = max(self._start_y, event.y)

        if (x2 - x1) > 30 and (y2 - y1) > 20:
            self._selected = True
            self.window.destroy()
            self.callback((x1, y1, x2 - x1, y2 - y1))
        else:
            if self._rect:
                self.canvas.delete(self._rect)
                self._rect = None
