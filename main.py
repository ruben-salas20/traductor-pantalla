"""
Traductor de Pantalla
─────────────────────
F2     → seleccionar región y traducir
Escape → detener traducción
Clic derecho en el ícono de la bandeja → Salir
"""

import threading
import tkinter as tk
from PIL import Image, ImageDraw
import pystray
import keyboard

from src.app import TranslatorApp
from src.ocr import OCREngine

HOTKEY_START = "f2"
HOTKEY_STOP  = "escape"

IDLE        = "idle"
SELECTING   = "selecting"
TRANSLATING = "translating"


def _make_tray_icon() -> Image.Image:
    """Genera un ícono simple para la bandeja del sistema."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill="#1a1a2e")
    d.text((18, 18), "T", fill="#90caf9")
    return img


class FloatingBar:
    def __init__(self):
        self.root   = tk.Tk()
        self.app    = TranslatorApp(self.root, on_status_change=self._on_status)
        self._state = IDLE
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self._register_hotkeys()
        self._start_tray()
        self._check_tesseract()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        self.root.title("Traductor")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.93)
        self.root.geometry("240x34+30+30")
        self.root.config(bg="#1a1a2e")

        self.lbl = tk.Label(
            self.root,
            text="Traductor  •  F2 para seleccionar",
            bg="#1a1a2e", fg="#90caf9",
            font=("Arial", 9),
            cursor="fleur",
        )
        self.lbl.pack(fill="both", expand=True, padx=10)

        for w in (self.root, self.lbl):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>",     self._drag_move)

    def _set_ui(self, text: str, color: str):
        self.lbl.config(text=text, fg=color)

    # ------------------------------------------------------------------ Arrastre

    def _drag_start(self, event: tk.Event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event: tk.Event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------ Bandeja del sistema

    def _start_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("Traductor de Pantalla", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Detener traducción", self._tray_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", self._tray_exit),
        )
        self._tray = pystray.Icon(
            "traductor",
            _make_tray_icon(),
            "Traductor de Pantalla\nF2 para seleccionar",
            menu,
        )
        threading.Thread(target=self._tray.run, daemon=True).start()

    def _tray_stop(self, icon=None, item=None):
        self.root.after(0, self._on_escape)

    def _tray_exit(self, icon=None, item=None):
        self._tray.stop()
        self.root.after(0, self._quit)

    def _quit(self):
        self.app.stop()
        self.root.destroy()

    # ------------------------------------------------------------------ Hotkeys

    def _register_hotkeys(self):
        keyboard.add_hotkey(HOTKEY_START, lambda: self.root.after(0, self._on_f2))
        keyboard.add_hotkey(HOTKEY_STOP,  lambda: self.root.after(0, self._on_escape))

    def _on_f2(self):
        if self._state == TRANSLATING:
            self.app.stop()
        self._state = SELECTING
        self._set_ui("Seleccionando región…  ESC cancela", "#fff176")
        self.root.withdraw()
        self.root.after(200, self._launch_selector)

    def _on_escape(self):
        if self._state == TRANSLATING:
            self.app.stop()
            self._state = IDLE
            self._set_ui("Traductor  •  F2 para seleccionar", "#90caf9")

    def _launch_selector(self):
        self.app.select_region(on_selected=self._before_overlay)
        if self._state == SELECTING:
            self._state = IDLE
            self._set_ui("Traductor  •  F2 para seleccionar", "#90caf9")
        self.root.deiconify()

    def _before_overlay(self):
        self.root.deiconify()
        self.root.update_idletasks()

    def _on_status(self, message: str):
        if "Traduciendo" in message:
            self._state = TRANSLATING
            self._set_ui("● Traduciendo  •  ESC para detener", "#80cbc4")
            self._tray.title = "Traductor • Traduciendo"
        else:
            self._state = IDLE
            self._set_ui("Traductor  •  F2 para seleccionar", "#90caf9")
            self._tray.title = "Traductor de Pantalla\nF2 para seleccionar"

    # ------------------------------------------------------------------ Misc

    def _check_tesseract(self):
        if not OCREngine().is_available():
            from tkinter import messagebox
            messagebox.showwarning(
                "Tesseract no encontrado",
                "Instala Tesseract OCR en:\n"
                "C:\\Program Files\\Tesseract-OCR\\"
            )

    def run(self):
        self.root.mainloop()
        self._tray.stop()


if __name__ == "__main__":
    FloatingBar().run()
