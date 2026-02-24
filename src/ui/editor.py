from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCharFormat, QColor


class ResultEditor(QTextEdit):
    """
    Read-only rich-text area for displaying sentence-level AI highlighting.

    Backend usage:
        Call highlight_sentences(sentences) with the list returned by your detector.
        Each item must be a dict with "text" (str) and "ai_probability" (float 0–100).

        Color mapping:
            ai_probability >= 70  →  red    (high AI likelihood)
            ai_probability >= 40  →  yellow (uncertain)
            ai_probability <  40  →  green  (likely human-written)

        Example:
            self._result_editor.highlight_sentences([
                {"text": "This sentence was written by AI.", "ai_probability": 85.0},
                {"text": "This one looks human.", "ai_probability": 20.0},
            ])
    """

    # (min_score, background_color, tooltip_label)
    _THRESHOLDS: list[tuple[float, QColor, str]] = [
        (70.0, QColor(255, 100, 100, 150), "High AI probability"),
        (40.0, QColor(255, 210,  80, 150), "Medium — uncertain"),
        ( 0.0, QColor(100, 200, 100, 150), "Likely human-written"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Detection results will appear here…")

    # ── BACKEND HOOK ──────────────────────────────────────────────────
    def highlight_sentences(self, sentences: list[dict]) -> None:
        """
        Render sentences with color-coded background highlights.

        Args:
            sentences: list of {"text": str, "ai_probability": float (0–100)}
        """
        self.clear()
        cursor = self.textCursor()

        for item in sentences:
            text = item.get("text", "")
            score = float(item.get("ai_probability", 0))

            bg_color, tooltip = self._score_to_fmt(score)
            fmt = QTextCharFormat()
            fmt.setBackground(bg_color)
            fmt.setToolTip(f"{tooltip} ({score:.0f}%)")

            cursor.insertText(text + " ", fmt)

        self.setTextCursor(cursor)
    # ── END BACKEND HOOK ──────────────────────────────────────────────

    @classmethod
    def _score_to_fmt(cls, score: float) -> tuple[QColor, str]:
        for threshold, color, label in cls._THRESHOLDS:
            if score >= threshold:
                return color, label
        return cls._THRESHOLDS[-1][1], cls._THRESHOLDS[-1][2]
