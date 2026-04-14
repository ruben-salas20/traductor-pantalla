import os
from typing import Dict, List, Optional

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Escala a la que ampliamos la imagen antes del OCR.
# 2.5x da buen balance entre precisión y velocidad para texto de UI.
_SCALE = 2.5

# Configuración de Tesseract:
# --psm 11 = texto disperso (ideal para UI con texto suelto)
# --oem 3  = motor LSTM (más preciso)
_TESS_CONFIG = "--psm 11 --oem 3"


class OCREngine:
    def __init__(self, tesseract_path: Optional[str] = None):
        path = tesseract_path or DEFAULT_TESSERACT_PATH
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path

    def is_available(self) -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_text_blocks(self, image: Image.Image, min_confidence: int = 40) -> List[Dict]:
        """
        Preprocesa la imagen y extrae bloques de texto con sus posiciones.
        Las coordenadas devueltas están en el espacio de la imagen original.
        """
        processed = self._preprocess(image)
        scale = processed.width / image.width  # factor real aplicado

        data = pytesseract.image_to_data(
            processed,
            lang="eng",
            config=_TESS_CONFIG,
            output_type=pytesseract.Output.DICT,
        )

        word_blocks = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if text and conf >= min_confidence:
                word_blocks.append(
                    {
                        "text": text,
                        # Convertir coordenadas de vuelta a la imagen original
                        "x": int(data["left"][i] / scale),
                        "y": int(data["top"][i] / scale),
                        "w": int(data["width"][i] / scale),
                        "h": int(data["height"][i] / scale),
                        "conf": conf,
                        "block_num": data["block_num"][i],
                        "line_num": data["line_num"][i],
                    }
                )

        return self._group_by_lines(word_blocks)

    def _preprocess(self, image: Image.Image) -> Image.Image:
        """
        Pipeline de preprocesamiento para mejorar la detección de texto
        pequeño típico de interfaces de usuario.
        """
        w, h = image.size

        # 1. Escalar (el paso más crítico para texto pequeño)
        new_w = int(w * _SCALE)
        new_h = int(h * _SCALE)
        image = image.resize((new_w, new_h), Image.LANCZOS)

        # 2. Convertir a escala de grises
        image = image.convert("L")

        # 3. Aumentar contraste para separar texto del fondo
        image = ImageEnhance.Contrast(image).enhance(2.0)

        # 4. Nitidez para bordes de letras más definidos
        image = image.filter(ImageFilter.SHARPEN)

        return image

    def _group_by_lines(self, word_blocks: List[Dict]) -> List[Dict]:
        """Agrupa palabras por línea para traducción más coherente."""
        if not word_blocks:
            return []

        lines: Dict = {}
        for block in word_blocks:
            key = (block["block_num"], block["line_num"])
            if key not in lines:
                lines[key] = {
                    "text": block["text"],
                    "x": block["x"],
                    "y": block["y"],
                    "x2": block["x"] + block["w"],
                    "y2": block["y"] + block["h"],
                }
            else:
                lines[key]["text"] += " " + block["text"]
                lines[key]["x2"] = max(lines[key]["x2"], block["x"] + block["w"])
                lines[key]["y2"] = max(lines[key]["y2"], block["y"] + block["h"])

        return [
            {
                "text": v["text"].strip(),
                "x": v["x"],
                "y": v["y"],
                "w": v["x2"] - v["x"],
                "h": v["y2"] - v["y"],
            }
            for v in lines.values()
            if v["text"].strip()
        ]
