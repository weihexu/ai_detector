# Core Layer — `src/core/`

Business logic and API integration. No PyQt6, no UI imports allowed here.

---

## Files

| File | Class / Role |
|---|---|
| `detector.py` | `Detector` — Gemini API client, implements `detect(text) -> dict` |
| `processor.py` | Text segmentation and input sanitisation (stub — implement with `nltk`) |

---

## `Detector` — required interface

The UI worker calls `detector.detect(text)` off the main thread. The return value drives the entire UI.

```python
class Detector:
    def detect(self, text: str) -> dict:
        ...
```

### Return contract

```python
{
    "overall_score": float,       # 0–100, overall AI probability
    "sentences": [
        {
            "text": str,              # sentence as it appears in the input
            "ai_probability": float,  # 0–100, per-sentence AI probability
        },
        # one entry per sentence
    ]
}
```

### On failure

Raise a descriptive exception. `DetectionWorker` catches all exceptions and routes them to `MainWindow.on_error()`. Do not return partial dicts with an `"error"` key — raise instead (it gives a cleaner stack trace).

---

## Current TODOs in `detector.py`

1. **Parse JSON** — `response.text` is a raw string from Gemini. Use `json.loads()` (strip markdown fences first if present) to turn it into the dict contract above.
2. **Read model from env** — replace the hardcoded `'gemini-pro'` string:
   ```python
   model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
   self.model = genai.GenerativeModel(model_name)
   ```

---

## `processor.py` — text segmentation

Use `nltk.sent_tokenize(text)` to split input into sentences before (or instead of) asking Gemini to segment them. Return `list[str]`.

```python
import nltk
nltk.download("punkt", quiet=True)

def split_sentences(text: str) -> list[str]:
    return nltk.sent_tokenize(text.strip())
```

Call this from `Detector.detect()` if you want to pre-segment before the API call.

---

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | Gemini API authentication | *(required)* |
| `GEMINI_MODEL` | Model ID to use | `gemini-2.0-flash` |

Access via `os.getenv(...)` only. `load_dotenv()` is called at the top of `detector.py` and loads from the project-root `.env` file. Never hardcode credentials.

---

## Rules

- No PyQt6 imports. No `ui/` imports.
- Raise on errors — do not silently swallow exceptions.
- Keep API-specific logic inside its own file so providers can be swapped cleanly.
- Use `os.getenv(...)` for all secrets.
