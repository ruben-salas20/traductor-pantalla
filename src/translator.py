from typing import Dict, List

from deep_translator import GoogleTranslator


class TranslationService:
    def __init__(self, source: str = "en", target: str = "es"):
        self._translator = GoogleTranslator(source=source, target=target)
        self._cache: Dict[str, str] = {}

    def translate_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """Añade el campo 'translated' a cada bloque de texto"""
        for block in blocks:
            text = block.get("text", "").strip()
            if text:
                block["translated"] = self._translate(text)
        return blocks

    def _translate(self, text: str) -> str:
        if text in self._cache:
            return self._cache[text]
        try:
            result = self._translator.translate(text)
            self._cache[text] = result or text
        except Exception:
            self._cache[text] = text
        return self._cache[text]
