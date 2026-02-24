# AI Detector — Quillbot Style

A lightweight desktop application built with PyQt6 that uses the Gemini API to detect AI-generated content. The app provides an overall probability score and sentence-level colour-coded highlighting, similar to Quillbot's AI Detector.

---

## Features

- **AI Probability Scoring** — percentage indicating the likelihood the text was AI-generated.
- **Sentence-Level Highlighting** — red / yellow / green coding by AI probability per sentence.
- **API Settings Dialog** — enter and save your Gemini API key and model without touching files.
- **Word Counter** — live word count as you type.
- **Non-blocking Detection** — runs in a `QThread`; the UI stays responsive during API calls.
- **Preview Mode** — run the UI with mock data, no API key needed (great for UI development).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| GUI | PyQt6 |
| AI Backend | Google Gemini API (`google-generativeai`) |
| Environment | `python-dotenv` |
| Text utilities | `nltk` |

---

## Project Structure

```
ai_detector/
├── src/
│   ├── main.py              # ← Primary entry point (production)
│   ├── preview.py           # ← Preview entry point (UI dev / no API key needed)
│   │
│   ├── ui/                  # Frontend layer — PyQt6 only, no API calls here
│   │   ├── main_window.py   # QMainWindow — layout, signals, on_result() hook
│   │   ├── editor.py        # ResultEditor — highlight_sentences() hook
│   │   ├── settings_dialog.py  # API key + model picker, writes to .env
│   │   └── worker.py        # DetectionWorker(QThread) — runs detect() off-thread
│   │
│   ├── core/                # Backend layer — business logic, no UI imports
│   │   ├── detector.py      # Detector class — Gemini API integration
│   │   └── processor.py     # Text segmentation / preprocessing (to be implemented)
│   │
│   └── agents/              # Agent modules — one file per provider
│       └── __init__.py
│
├── .env                     # Local credentials (git-ignored)
├── .env.example             # Template — copy to .env and fill in
├── requirements.txt         # Python dependencies
├── context.md               # Agent delegation & architecture notes
└── README.md
```

---

## Setup

```bash
# 1. Clone
git clone <repo-url>
cd ai_detector

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env from template
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux

# 5. Add your Gemini API key to .env
#    GEMINI_API_KEY=AIza...
#    GEMINI_MODEL=gemini-2.0-flash
```

---

## Entry Points

### Production — `src/main.py`

The standard launch path. Requires a valid `GEMINI_API_KEY` in `.env` (or entered via the in-app Settings dialog).

```bash
cd src
python main.py
```

### Preview / UI Development — `src/preview.py`

Launches the full UI with mock detection data injected automatically. **No API key required.** Use this to work on layout, colours, and result rendering without making any API calls.

```bash
cd src
python preview.py
```

The preview injects `MOCK_RESULT` (defined at the top of `preview.py`) into `MainWindow.on_result()` after 800 ms, exercising the exact same code path as a live detection.

To test different score distributions, edit `MOCK_RESULT` in `preview.py` — no other changes needed.

---

## Backend Integration Guide

This section is for engineers working on `src/core/` or `src/agents/`.

### The data contract

Every detection result must be a plain Python `dict` with this exact shape:

```python
{
    "overall_score": float,       # 0–100, overall AI probability
    "sentences": [
        {
            "text": str,          # the sentence as it appears in the input
            "ai_probability": float,  # 0–100, per-sentence AI probability
        },
        # ...one entry per sentence
    ]
}
```

On failure, return or raise — do **not** return a partial dict.
The worker catches all exceptions and surfaces them via `on_error()`.

### Hook sites — marked in source

Every integration point in the UI code is wrapped in a comment block:

```python
# ── BACKEND HOOK ──────────────────────────────────────────
...
# ── END BACKEND HOOK ──────────────────────────────────────
```

The three that matter most:

| File | Location | What to do |
|---|---|---|
| `ui/main_window.py` | `__init__` | Swap `Detector()` for your own detector class |
| `ui/main_window.py` | `on_result(result)` | Called automatically with the result dict |
| `ui/worker.py` | `run()` | Replace/extend the `self._detector.detect()` call |

### Swapping the detector

Any object with a `detect(text: str) -> dict` method works:

```python
# In ui/main_window.py __init__, replace:
self._detector = Detector()

# With your own class:
self._detector = MyCustomDetector()
```

`MyCustomDetector` just needs to implement:

```python
class MyCustomDetector:
    def detect(self, text: str) -> dict:
        # your logic here
        return {
            "overall_score": 72.0,
            "sentences": [{"text": "...", "ai_probability": 72.0}],
        }
```

### Threading model

```
Main thread (Qt event loop)
│
├── User clicks "Detect AI"
│   └── MainWindow._start_detection()
│       └── DetectionWorker(QThread).start()
│
└── Worker thread
    └── DetectionWorker.run()
        └── detector.detect(text)   ← your code runs here, off the main thread
            │
            ├── success → emits result_ready(dict)
            │             → MainWindow.on_result(dict)  ← back on main thread
            │
            └── failure → emits error_occurred(str)
                          → MainWindow.on_error(str)   ← back on main thread
```

Never call Qt widget methods from inside `detect()`. Signals handle the thread boundary automatically.

### Adding a new model / provider

1. Add your agent class in `src/agents/<provider>_agent.py` — implement `detect(text: str) -> dict`.
2. Add any new model names to `AVAILABLE_MODELS` in `src/ui/settings_dialog.py`.
3. In `MainWindow.__init__`, swap `Detector()` for your agent.

---

## Colour Reference

| Colour | Threshold | Meaning |
|---|---|---|
| Red | `ai_probability >= 70` | High AI likelihood |
| Yellow | `ai_probability >= 40` | Uncertain |
| Green | `ai_probability < 40` | Likely human-written |

Thresholds are defined in `ui/editor.py → ResultEditor._THRESHOLDS`. Edit there to change the breakpoints globally.
