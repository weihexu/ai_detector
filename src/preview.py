"""
Preview launcher — shows the full UI with mock detection data injected
automatically after a short delay. No API key required.

Use this to develop, style, or test the UI without a live Gemini connection.

Usage:
    cd src
    python preview.py

What it does:
    1. Launches MainWindow normally.
    2. Pre-fills the input editor with sample text.
    3. After 800 ms, calls window.on_result(MOCK_RESULT) — the same slot the
       real backend calls — so you see exactly how the UI behaves with real data.

Customising the mock data:
    Edit MOCK_RESULT below to test different score ranges and sentence counts.
    The dict must match the contract described in ui/main_window.py (on_result).
"""

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

# ── Mock payload ──────────────────────────────────────────────────────────────
# Shape must match: {"overall_score": float, "sentences": [{"text": str, "ai_probability": float}]}
MOCK_RESULT: dict = {
    "overall_score": 73.5,
    "sentences": [
        {
            "text": "The quick brown fox jumps over the lazy dog.",
            "ai_probability": 14.0,
        },
        {
            "text": (
                "This particular sentence was most likely generated "
                "by an artificial intelligence system."
            ),
            "ai_probability": 92.0,
        },
        {
            "text": "Language models tend to produce very fluent and coherent prose.",
            "ai_probability": 87.0,
        },
        {
            "text": "However, some passages feel more natural and human in tone.",
            "ai_probability": 36.0,
        },
        {
            "text": "The distinction is not always immediately obvious to the reader.",
            "ai_probability": 58.0,
        },
    ],
}

_MOCK_INPUT = " ".join(s["text"] for s in MOCK_RESULT["sentences"])
# ── End mock payload ──────────────────────────────────────────────────────────


def main() -> None:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.setWindowTitle("AI Detector — Preview Mode")
    window.show()

    # Pre-fill input so the word counter and layout look realistic
    window._input_editor.setPlainText(_MOCK_INPUT)

    # Simulate the async result arriving from the backend
    QTimer.singleShot(800, lambda: window.on_result(MOCK_RESULT))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
