# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python main.py
```

Requires Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.  
Install dependencies: `pip install -r requirements.txt` (also needs `pip install keyboard`).

## Architecture

The app is a real-time screen translator (English → Spanish) for Windows. One `tk.Tk()` root is created in `main.py` and passed down to every component — this is mandatory because tkinter is not thread-safe and all UI operations must happen on the main thread via `root.after(0, ...)`.

**Data flow:**
```
F2 hotkey → RegionSelector (modal Toplevel) → TranslatorApp._loop() [background thread]
    → ScreenCapture (mss) → OCREngine (pytesseract) → TranslationService (deep-translator)
    → TranslationOverlay.update_translations() → Queue → _poll() [main thread] → canvas draw
```

**Key design decisions:**

- **Single `tk.Tk()` root**: `RegionSelector` and `TranslationOverlay` are both `Toplevel` windows sharing the same root. Never create a second `tk.Tk()`.
- **Thread communication**: The background loop writes translated blocks to a `queue.Queue`; the overlay drains it every 100ms via `window.after()`. Do not call tkinter methods directly from the background thread.
- **mss thread-safety**: `mss.mss()` uses thread-local storage — instantiate it inside the method that uses it (`with mss.mss() as sct:`), never store it as an instance variable.
- **Overlay positioning**: The translation panel sits **below** the selected source region (never over it). This avoids mss capturing the overlay's dark background instead of the actual screen content.
- **Alpha + click-through**: After calling `SetWindowLong(WS_EX_LAYERED | WS_EX_TRANSPARENT)`, always re-apply alpha with `SetLayeredWindowAttributes` — modifying `GWL_EXSTYLE` resets the layered window state on Windows, leaving the window invisible (alpha=0).
- **`overrideredirect(True)` windows**: Use `withdraw()` / `deiconify()` to hide/show — `iconify()` raises `TclError`.
- **OCR preprocessing**: Images are scaled 2.5× before Tesseract with `--psm 11 --oem 3`. Bounding box coordinates are divided back by the scale factor before use.
- **Translation quality**: All OCR text blocks are joined into a single string and translated in one call — per-line translation loses context.

## Module responsibilities

| File | Responsibility |
|---|---|
| `main.py` | `FloatingBar` UI (overrideredirect, draggable), global hotkeys via `keyboard` library |
| `src/app.py` | `TranslatorApp` — coordinates the capture/OCR/translate loop in a daemon thread |
| `src/overlay.py` | `TranslationOverlay` — Toplevel panel below source region; Queue-based thread-safe updates; Windows alpha+click-through via ctypes |
| `src/selector.py` | `RegionSelector` — fullscreen Toplevel for drag-to-select; blocks via `wait_window()` |
| `src/capture.py` | `ScreenCapture` — wraps mss; creates instance per call for thread safety |
| `src/ocr.py` | `OCREngine` — pytesseract wrapper with 2.5× upscale + contrast preprocessing |
| `src/translator.py` | `TranslationService` — deep-translator with in-memory cache |
