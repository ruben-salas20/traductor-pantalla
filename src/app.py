import threading
import time
import tkinter as tk
from typing import Callable, Optional, Tuple

from .capture import ScreenCapture
from .ocr import OCREngine
from .overlay import TranslationOverlay
from .selector import RegionSelector
from .translator import TranslationService


class TranslatorApp:
    """
    Coordinador principal. Recibe el root de tkinter para que el overlay
    y el selector compartan el mismo intérprete Tcl y los updates de UI
    puedan despacharse de forma segura desde el hilo secundario.
    """

    def __init__(self, root: tk.Tk, on_status_change: Optional[Callable[[str], None]] = None):
        self._root = root
        self._on_status_change = on_status_change

        self.capture = ScreenCapture()
        self.ocr = OCREngine()
        self.translator = TranslationService(source="en", target="es")
        self.overlay = TranslationOverlay(root)

        self.region: Optional[Tuple[int, int, int, int]] = None
        self.running = False
        self.interval = 1.5

        self._thread: Optional[threading.Thread] = None
        self._last_hash: Optional[int] = None
        self._on_selected_cb: Optional[Callable] = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def select_region(self, on_selected=None):
        """
        Abre el selector modal. on_selected se llama justo antes de mostrar
        el overlay, para que el caller pueda restaurar ventanas primero.
        """
        self.stop()
        self._on_selected_cb = on_selected
        RegionSelector(self._root, callback=self._on_region_selected).start()

    def start(self):
        if self.running or not self.region:
            return
        self.overlay.show(self.region)
        self.running = True
        self._last_hash = None
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._notify("Traduciendo…")

    def stop(self):
        self.running = False
        self.overlay.hide()
        self._last_hash = None
        self._notify("Detenido")

    def set_interval(self, seconds: float):
        self.interval = max(0.5, seconds)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _on_region_selected(self, region: Tuple[int, int, int, int]):
        self.region = region
        # Avisar al caller antes de crear el overlay (ej: para deiconify)
        if self._on_selected_cb:
            self._on_selected_cb()
            self._on_selected_cb = None
        self.start()

    def _loop(self):
        while self.running:
            try:
                # El panel de traducción está debajo de la región fuente,
                # nunca la tapa → captura directa sin ocultar nada
                image = self.capture.capture_region(self.region)
                current_hash = self.capture.get_image_hash(image)

                if current_hash != self._last_hash:
                    self._last_hash = current_hash
                    blocks = self.ocr.extract_text_blocks(image)
                    if blocks:
                        full_text  = " ".join(b["text"] for b in blocks)
                        translated = self.translator._translate(full_text)
                        self.overlay.update_translations([{"translated": translated}])
                    else:
                        self.overlay.update_translations([])

            except Exception as e:
                import traceback
                print(f"[app] error en el loop: {e}")
                traceback.print_exc()

            time.sleep(self.interval)

    def _notify(self, message: str):
        if self._on_status_change:
            self._root.after(0, lambda m=message: self._on_status_change(m))
