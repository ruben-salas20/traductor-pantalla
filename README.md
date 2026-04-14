# Traductor de Pantalla

Traduce en tiempo real cualquier región de la pantalla de **inglés a español** en Windows. Similar a Google Lens pero para escritorio.

## Cómo funciona

1. Presiona **F2** → arrastra para seleccionar el área con texto en inglés
2. El panel de traducción aparece automáticamente debajo del texto
3. Presiona **ESC** para detener
4. La barra flotante se puede arrastrar a cualquier posición de la pantalla

## Requisitos

- Windows 10/11
- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado en `C:\Program Files\Tesseract-OCR\`

## Instalación

```bash
pip install -r requirements.txt
pip install keyboard
```

## Uso

**Con consola** (para ver errores):
```bash
python main.py
```

**Sin consola** (uso normal):
Doble clic en `iniciar.vbs`

### Arranque automático con Windows

Para que el traductor inicie con Windows, crea un acceso directo de `iniciar.vbs` y colócalo en:
```
C:\Users\<tu_usuario>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

## Tecnologías

- **OCR**: Tesseract + pytesseract (escala 2.5× + mejora de contraste)
- **Traducción**: Google Translate vía deep-translator (gratuito, sin API key)
- **Captura**: mss
- **UI**: tkinter
