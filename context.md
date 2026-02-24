# AI Detector — Agent Delegation & Architecture

This document is the top-level directive for AI agents (Claude Code, etc.) working on this project. It defines architectural boundaries, responsibilities, and current integration contracts.

---

## Project Vision

A high-fidelity AI text detector using PyQt6 and the Gemini API, mimicking Quillbot's AI Detector aesthetic. The app must provide an overall probability percentage and sentence-level colour-coded feedback.

---

## Entry Points

| File | Purpose |
|---|---|
| `src/main.py` | **Production launcher** — requires `GEMINI_API_KEY` in `.env` |
| `src/preview.py` | **UI preview launcher** — injects mock data, no API key needed |

Run from the `src/` directory:

```bash
python main.py      # production
python preview.py   # UI preview / development
```

---

## Current File Map

```
src/
├── main.py              # Entry point — creates QApplication and MainWindow
├── preview.py           # Preview entry point — mock data, no API required
│
├── ui/
│   ├── main_window.py   # QMainWindow layout + signal wiring + backend hooks
│   ├── editor.py        # ResultEditor(QTextEdit) — highlight_sentences()
│   ├── settings_dialog.py  # API key + model picker dialog, writes .env
│   └── worker.py        # DetectionWorker(QThread) — off-thread detection
│
├── core/
│   ├── detector.py      # Detector class — Gemini API client
│   └── processor.py     # Text segmentation / sanitisation (stub)
│
└── agents/
    └── __init__.py      # Agent modules go here (one file per provider)
```

---

## Agent Delegations

### 1. UI/UX Specialist — `src/ui/`

**Do not import from `core/` directly** except in `main_window.py`. Do not call network I/O on the main thread.

**`main_window.py`**
- Owns the full window layout (header, input editor, action bar, score bar, result editor).
- Exposes two public slots for the backend to call or connect to:
  - `on_result(result: dict)` — receives the detection dict, updates score bar and result editor.
  - `on_error(message: str)` — surfaces error text in the result editor and status bar.
- Backend hook sites are marked `── BACKEND HOOK ──` in the source.

**`editor.py`**
- `ResultEditor.highlight_sentences(sentences: list[dict])` — the single public method backend engineers interact with.
- Colour thresholds live in `ResultEditor._THRESHOLDS`; edit there to change breakpoints.

**`settings_dialog.py`**
- `AVAILABLE_MODELS` list at the top — add/remove Gemini model IDs here.
- Saves `GEMINI_API_KEY` and `GEMINI_MODEL` to the project-root `.env` and `os.environ`.

**`worker.py`**
- `DetectionWorker(QThread)` calls `detector.detect(text)` off the main thread.
- Emits `result_ready(dict)` on success, `error_occurred(str)` on failure.
- To swap the detector: pass a different object to `DetectionWorker(detector, text)`.

---

### 2. Backend & Core Engineer — `src/core/`

**Do not import PyQt6 or any `ui/` module here.**

**`detector.py`** — `Detector` class
- Reads `GEMINI_API_KEY` and `GEMINI_MODEL` from `os.environ` (populated by `load_dotenv()` or the settings dialog).
- Must implement: `detect(text: str) -> dict`
- Return contract (required by the UI):
  ```python
  {
      "overall_score": float,        # 0–100
      "sentences": [
          {"text": str, "ai_probability": float},  # 0–100
          # ...
      ]
  }
  ```
- On failure: raise an exception (worker catches it) or return `{"error": str}`.
- **TODO**: Parse Gemini's response text as JSON — currently returns raw `response.text`.
- **TODO**: Read model name from `os.getenv("GEMINI_MODEL", "gemini-2.0-flash")` instead of hardcoding `"gemini-pro"`.

**`processor.py`** — text segmentation (stub)
- Implement sentence splitting (use `nltk.sent_tokenize` — already in requirements).
- Sanitise input before it reaches the API.
- Output: `list[str]` of cleaned sentence strings.

---

### 3. Agent Modules — `src/agents/`

- One file per provider (e.g., `gemini_agent.py`, `openai_agent.py`).
- Class name convention: `<Provider>Agent` (e.g., `GeminiAgent`).
- Each must implement:
  ```python
  def detect(self, text: str) -> dict:
      # Returns: {"overall_score": float, "sentences": [{"text": str, "ai_probability": float}]}
  ```
- No PyQt6 imports. No UI imports. Raise on API errors; let the caller handle fallback.
- API keys via `os.getenv(...)` only — never hardcoded.

To wire a new agent into the UI, in `ui/main_window.py`:
```python
# Replace:
self._detector = Detector()
# With:
from agents.gemini_agent import GeminiAgent
self._detector = GeminiAgent()
```

---

### 4. Infrastructure — Project Root

**`.env.example`** — template for required environment variables:
```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

**`requirements.txt`** — current dependencies: `PyQt6`, `google-generativeai`, `python-dotenv`, `nltk`.

**`preview.py`** — UI smoke-test without API:
- Edit `MOCK_RESULT` at the top to test different score distributions.
- The mock is injected via `MainWindow.on_result()` — same code path as live results.

---

## Data Flow

```
[User pastes text]
        │
        ▼
MainWindow._start_detection()
        │
        ▼
DetectionWorker(QThread).start()
        │  (off main thread)
        ▼
detector.detect(text)          ← implement / swap here
        │
        ├─ success ──► result_ready(dict)
        │                     │
        │                     ▼
        │             MainWindow.on_result(dict)
        │                     │
        │              ┌──────┴──────┐
        │              ▼             ▼
        │        score bar     ResultEditor
        │        updated       .highlight_sentences()
        │
        └─ failure ──► error_occurred(str)
                              │
                              ▼
                      MainWindow.on_error(str)
```

---

## Technical Constraints

1. **Thread safety** — never call Qt widget methods from `detect()` or any background thread.
2. **Response format** — all detection results must match the dict contract above before reaching the UI.
3. **No cross-layer imports** — `core/` and `agents/` must not import from `ui/`.
4. **Credentials** — always `os.getenv(...)`, never hardcoded.
