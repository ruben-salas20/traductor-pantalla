import ctypes
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, List, Optional, Tuple

_OVERLAY_BG = "#0d1b2a"
_OVERLAY_ALPHA = 0.92
_TEXT_COLOR = "#ffffff"
_BORDER_COLOR = "#1e6ba8"
_FONT = "Arial"
_POLL_MS = 100
_LINE_HEIGHT = 22   # px por línea de texto traducido
_PADDING = 8        # padding interno del panel


class TranslationOverlay:
    def __init__(self, root: tk.Tk):
        self._root = root
        self.window: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self._queue: queue.Queue = queue.Queue()
        self._source_region: Optional[Tuple[int, int, int, int]] = None

    def show(self, region: Tuple[int, int, int, int]):
        """Crea el panel de traducción. Debe llamarse desde el hilo principal."""
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass

        self._source_region = region
        x, y, w, h = region

        # Posicionar el panel debajo de la región fuente (o arriba si no hay espacio)
        panel_h = _LINE_HEIGHT + _PADDING * 2
        screen_h = self._root.winfo_screenheight()
        if y + h + panel_h + 4 <= screen_h:
            panel_y = y + h + 2
        else:
            panel_y = y - panel_h - 2

        pass  # show

        self.window = tk.Toplevel(self._root)
        self.window.geometry(f"{w}x{panel_h}+{x}+{panel_y}")
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)
        self.window.config(bg=_OVERLAY_BG)

        self.canvas = tk.Canvas(
            self.window, bg=_OVERLAY_BG, highlightthickness=1,
            highlightbackground=_BORDER_COLOR, bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.window.update_idletasks()
        self.window.lift()
        self._apply_alpha_clickthrough()

        self._start_poll()

    def _apply_alpha_clickthrough(self):
        """Aplica alpha + click-through en una sola llamada para evitar reset del estado layered."""
        try:
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            LWA_ALPHA = 0x2

            hwnd = self.window.winfo_id()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            )
            alpha = int(_OVERLAY_ALPHA * 255)
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)
            pass  # alpha ok
        except Exception as e:
            print(f"[overlay] error aplicando alpha/click-through: {e}")

    def _resize_panel(self, n_lines: int):
        """Ajusta la altura del panel según el número de líneas a mostrar."""
        if not self.window or not self._source_region:
            return
        x, y, w, h = self._source_region
        panel_h = max(_LINE_HEIGHT, n_lines * _LINE_HEIGHT) + _PADDING * 2
        screen_h = self._root.winfo_screenheight()
        if y + h + panel_h + 4 <= screen_h:
            panel_y = y + h + 2
        else:
            panel_y = y - panel_h - 2
        self.window.geometry(f"{w}x{panel_h}+{x}+{panel_y}")

    # ------------------------------------------------------------------
    # API hilo-segura
    # ------------------------------------------------------------------

    def update_translations(self, blocks: List[Dict]):
        """Puede llamarse desde cualquier hilo."""
        self._queue.put(blocks)

    def _start_poll(self):
        self._poll()

    def _poll(self):
        if not self.window:
            return
        try:
            blocks = None
            while not self._queue.empty():
                blocks = self._queue.get_nowait()
            if blocks is not None:
                self._draw(blocks)
        except queue.Empty:
            pass
        self.window.after(_POLL_MS, self._poll)

    def _calc_panel_height(self, text: str, available_width: int, font_size: int) -> int:
        """Calcula cuántos píxeles de alto necesita el panel para mostrar el texto."""
        f = tkfont.Font(family=_FONT, size=font_size, weight="bold")
        line_h = f.metrics("linespace")
        # Contar líneas estimadas por word-wrap
        words = text.split()
        lines = 1
        current_w = 0
        for word in words:
            ww = f.measure(word + " ")
            if current_w + ww > available_width:
                lines += 1
                current_w = ww
            else:
                current_w += ww
        return lines * line_h + _PADDING * 2

    def _draw(self, blocks: List[Dict]):
        if not self.canvas or not self.window or not self._source_region:
            return

        translated = blocks[0].get("translated", "").strip() if blocks else ""
        if not translated:
            self.canvas.delete("all")
            return

        x, y, w, h = self._source_region
        available_w = w - _PADDING * 2
        font_size = 11

        # Calcular altura necesaria y redimensionar panel
        panel_h = self._calc_panel_height(translated, available_w, font_size)
        screen_h = self._root.winfo_screenheight()
        if y + h + panel_h + 4 <= screen_h:
            panel_y = y + h + 2
        else:
            panel_y = y - panel_h - 2
        self.window.geometry(f"{w}x{panel_h}+{x}+{panel_y}")

        self.canvas.delete("all")
        self.canvas.create_text(
            _PADDING, _PADDING,
            text=translated,
            fill=_TEXT_COLOR,
            anchor="nw",
            font=(_FONT, font_size, "bold"),
            width=available_w,
        )

    def hide(self):
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
            self.canvas = None

    def is_visible(self) -> bool:
        return self.window is not None
