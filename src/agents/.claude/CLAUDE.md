# Agents Layer — `src/agents/`

Agent modules for interacting with external AI APIs. One file per provider.

---

## Structure

- Each agent is a self-contained class.
- Agents are consumed by `src/core/detector.py` or wired directly into `MainWindow` — they do not touch the UI themselves.
- Keep API-specific logic isolated so swapping providers requires changing one line in `main_window.py`.

---

## Naming Convention

- File: `<provider>_agent.py` (e.g., `gemini_agent.py`, `openai_agent.py`)
- Class: `<Provider>Agent` (e.g., `GeminiAgent`, `OpenAIAgent`)

---

## Required Interface

Every agent must implement `detect`:

```python
def detect(self, text: str) -> dict:
    """
    Returns:
        {
            "overall_score": float,       # 0–100
            "sentences": [
                {"text": str, "ai_probability": float},  # 0–100
                ...
            ]
        }
    Raises:
        Exception — on API error. Let the caller (DetectionWorker) handle it.
    """
```

---

## Wiring an Agent into the UI

In `src/ui/main_window.py`, inside the `── BACKEND HOOK ──` block in `__init__`:

```python
# Replace:
from core.detector import Detector
self._detector = Detector()

# With your agent:
from agents.gemini_agent import GeminiAgent
self._detector = GeminiAgent()
```

No other UI changes are needed — the worker and signal chain stay the same.

---

## Environment

- Load credentials via `python-dotenv` — already called in `core/detector.py` at import time.
- Use `os.getenv("GEMINI_API_KEY")` — never hardcode.
- Use `os.getenv("GEMINI_MODEL", "gemini-2.0-flash")` for model selection.

---

## Rules

- No PyQt6 imports.
- No imports from `src/ui/`.
- Raise descriptive exceptions on API errors; the `DetectionWorker` catches them.
