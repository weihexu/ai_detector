from PyQt6.QtCore import QThread, pyqtSignal


class DetectionWorker(QThread):
    """
    Background thread that runs AI detection without blocking the UI.

    Signals:
        result_ready(dict):  Emitted on success.
            Shape: {
                "overall_score": float (0–100),
                "sentences": [
                    {"text": str, "ai_probability": float (0–100)},
                    ...
                ]
            }
        error_occurred(str): Emitted on failure with a human-readable message.

    Backend usage:
        Pass any detector object that implements detect(text: str) -> dict.
        Connect result_ready / error_occurred to your slots, then call start().

        Example:
            worker = DetectionWorker(my_detector, text, parent=self)
            worker.result_ready.connect(self.on_result)
            worker.error_occurred.connect(self.on_error)
            worker.start()
    """

    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, detector, text: str, parent=None):
        super().__init__(parent)
        self._detector = detector
        self._text = text

    def run(self) -> None:
        # ── BACKEND HOOK ─────────────────────────────────────────────
        # Swap self._detector for any object whose detect(text) returns the dict
        # described in the class docstring, or {"error": str} on failure.
        # Do NOT touch anything above or below this block.
        try:
            result = self._detector.detect(self._text)
            if isinstance(result, dict) and "error" in result:
                self.error_occurred.emit(str(result["error"]))
            else:
                self.result_ready.emit(result)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
        # ── END BACKEND HOOK ─────────────────────────────────────────
