import mss
from PIL import Image
from typing import Tuple


class ScreenCapture:
    def capture_region(self, region: Tuple[int, int, int, int]) -> Image.Image:
        """Captura una región de pantalla. region = (x, y, ancho, alto)"""
        x, y, w, h = region
        monitor = {"top": y, "left": x, "width": w, "height": h}
        # mss usa almacenamiento local de hilo: se debe crear en el mismo hilo que lo usa
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    def get_image_hash(self, image: Image.Image) -> int:
        """Hash rápido para detectar si la pantalla cambió"""
        thumb = image.resize((32, 32)).convert("L")
        return hash(thumb.tobytes())
