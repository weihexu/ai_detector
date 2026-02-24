# UI Layer — `src/ui/`

PyQt6 frontend only. No API calls, no network I/O, no imports from `core/` except in `main_window.py`.

---

## Files

| File | Class | Role |
|---|---|---|
| `main_window.py` | `MainWindow` | Full window layout, signal wiring, backend hooks |
| `editor.py` | `ResultEditor` | Read-only result viewer with sentence highlighting |
| `settings_dialog.py` | `SettingsDialog` | API key entry and model selection |
| `worker.py` | `DetectionWorker` | `QThread` wrapper — runs `detect()` off the main thread |

---

## Entry Points

**Production:**
```bash
cd src
python main.py
```

**Preview (no API key needed):**
```bash
cd src
python preview.py
```
`preview.py` calls `MainWindow.on_result(MOCK_RESULT)` after 800 ms, exercising the exact same rendering code path as a live result.

---

## Backend Integration Points

All sites are marked `── BACKEND HOOK ──` in the source. The two primary ones:

### 1. Swap the detector — `main_window.py __init__`

```python
# ── BACKEND HOOK ──
self._detector = Detector()   # replace with your class
# ── END BACKEND HOOK ──
```

Any object with `detect(text: str) -> dict` works.

### 2. Receive results — `MainWindow.on_result(result: dict)`

```python
@pyqtSlot(dict)
def on_result(self, result: dict) -> None:
    ...
```

Called automatically via signal when `DetectionWorker` finishes. Can also be called directly for testing:

```python
window.on_result({
    "overall_score": 72.0,
    "sentences": [{"text": "...", "ai_probability": 72.0}],
})
```

### 3. Receive errors — `MainWindow.on_error(message: str)`

```python
window.on_error("Something went wrong")
```

---

## Result Dict Contract

```python
{
    "overall_score": float,       # 0–100
    "sentences": [
        {
            "text": str,              # sentence text
            "ai_probability": float,  # 0–100
        },
    ]
}
```

---

## Colour Thresholds

Defined in `editor.py → ResultEditor._THRESHOLDS`. Edit there to change breakpoints globally.

| Range | Colour | Label |
|---|---|---|
| >= 70 | Red | High AI probability |
| >= 40 | Yellow | Medium / uncertain |
| < 40 | Green | Likely human-written |

---

## Available Models List

Defined in `settings_dialog.py → AVAILABLE_MODELS`. Add/remove model IDs there.

---

## Rules

- Do not import PyQt6 outside `src/ui/`.
- Do not call `detect()` or any network operation on the main thread — always via `DetectionWorker`.
- Do not read `.env` or call `load_dotenv()` here; that's the core layer's job.
