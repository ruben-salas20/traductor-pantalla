"""
Traductor de Pantalla
─────────────────────
F2     → seleccionar región y traducir
Escape → detener traducción
La barra flotante se puede arrastrar a cualquier posición.
"""

import tkinter as tk
import keyboard

from src.app import TranslatorApp
from src.ocr import OCREngine

HOTKEY_START = "f2"
HOTKEY_STOP  = "escape"

# Estados posibles
IDLE        = "idle"
SELECTING   = "selecting"
TRANSLATING = "translating"


class FloatingBar:
    """
    Barra pequeña siempre-encima que muestra el estado y registra
    los hotkeys globales. Se puede arrastrar con el ratón.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.app  = TranslatorApp(self.root, on_status_change=self._on_status)
        self._state   = IDLE
        self._drag_x  = 0
        self._drag_y  = 0

        self._build_ui()
        self._register_hotkeys()
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

        # Arrastre
        for w in (self.root, self.lbl):
            w.bind("<ButtonPress-1>",  self._drag_start)
            w.bind("<B1-Motion>",      self._drag_move)

        # Botón cerrar con doble clic
        self.root.bind("<Double-Button-1>", lambda _: self.root.destroy())
        self.lbl.bind("<Double-Button-1>",  lambda _: self.root.destroy())

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

    # ------------------------------------------------------------------ Hotkeys

    def _register_hotkeys(self):
        keyboard.add_hotkey(HOTKEY_START, lambda: self.root.after(0, self._on_f2))
        keyboard.add_hotkey(HOTKEY_STOP,  lambda: self.root.after(0, self._on_escape))

    def _on_f2(self):
        if self._state == TRANSLATING:
            # Re-seleccionar: detener primero
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
        # Llega aquí tras cerrar el selector (éxito o ESC)
        if self._state == SELECTING:
            # Usuario canceló con ESC sin seleccionar
            self._state = IDLE
            self._set_ui("Traductor  •  F2 para seleccionar", "#90caf9")
        self.root.deiconify()  # deiconify works fine with overrideredirect

    def _before_overlay(self):
        """Llamado justo antes de mostrar el overlay (desde app.py)."""
        self.root.deiconify()  # deiconify works fine with overrideredirect
        self.root.update_idletasks()

    def _on_status(self, message: str):
        if "Traduciendo" in message:
            self._state = TRANSLATING
            self._set_ui("● Traduciendo  •  ESC para detener", "#80cbc4")
        else:
            self._state = IDLE
            self._set_ui("Traductor  •  F2 para seleccionar", "#90caf9")

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


if __name__ == "__main__":
    FloatingBar().run()
