import os

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction

from ui.editor import ResultEditor
from ui.settings_dialog import AVAILABLE_MODELS, SettingsDialog
from ui.worker import DetectionWorker
from core.detector import Detector


class MainWindow(QMainWindow):
    """
    Primary application window.

    ┌─────────────────────────────────────────────────────┐
    │  [File]  [Settings]                                 │  ← menu bar
    ├─────────────────────────────────────────────────────┤
    │  Model: [combo ▼]   ● API status   [API Settings…] │  ← header
    ├─────────────────────────────────────────────────────┤
    │  Input Text                                         │
    │  ┌────────────────────────────────────────────┐     │
    │  │ Paste text here…                           │     │  ← input area
    │  └────────────────────────────────────────────┘     │
    │  [Detect AI]  [Clear]              Words: 0         │  ← action bar
    ├─────────────────────────────────────────────────────┤
    │  AI Score: ████████████░░░░  --%  ■High ■Med ■Human │  ← score bar
    ├─────────────────────────────────────────────────────┤
    │  Detection Results                                  │
    │  ┌────────────────────────────────────────────┐     │
    │  │ (highlighted sentences appear here)        │     │  ← results
    │  └────────────────────────────────────────────┘     │
    ├─────────────────────────────────────────────────────┤
    │  Ready                                              │  ← status bar
    └─────────────────────────────────────────────────────┘

    Backend integration:
        • Implement / swap Detector in core/detector.py.
          It must expose:  detect(text: str) -> dict
          Return shape:    {"overall_score": float, "sentences": [...]}
        • DetectionWorker (ui/worker.py) calls detector.detect() off-thread
          and emits result_ready(dict) → on_result(dict) here.
        • All backend hook sites are marked with ── BACKEND HOOK ── comments.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Detector")
        self.resize(920, 720)
        self.setMinimumSize(640, 500)

        # ── BACKEND HOOK ──────────────────────────────────────────
        # Swap Detector() for any class that implements detect(str) -> dict.
        self._detector = Detector()
        # ── END BACKEND HOOK ──────────────────────────────────────

        self._worker: DetectionWorker | None = None

        self._build_menu()
        self._build_central_widget()
        self._build_status_bar()
        self._refresh_api_status()

    # ──────────────────────────────────────────────────────────────
    # Construction helpers
    # ──────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        settings_menu = mb.addMenu("Settings")
        api_act = QAction("API Settings…", self)
        api_act.triggered.connect(self._open_settings)
        settings_menu.addAction(api_act)

    def _build_central_widget(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        self.setCentralWidget(root)

        layout.addLayout(self._make_header())
        layout.addWidget(_separator())

        # Input label + editor
        layout.addWidget(QLabel("Input Text"))
        self._input_editor = QTextEdit()
        self._input_editor.setPlaceholderText(
            "Paste the text you want to analyze here…"
        )
        self._input_editor.setMinimumHeight(160)
        self._input_editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input_editor, stretch=2)

        layout.addLayout(self._make_action_bar())
        layout.addLayout(self._make_score_bar())
        layout.addWidget(_separator())

        # Results label + editor
        layout.addWidget(QLabel("Detection Results"))
        self._result_editor = ResultEditor()
        self._result_editor.setMinimumHeight(160)
        layout.addWidget(self._result_editor, stretch=2)

    def _make_header(self) -> QHBoxLayout:
        row = QHBoxLayout()

        row.addWidget(QLabel("Model:"))
        self._model_combo = QComboBox()
        self._model_combo.addItems(AVAILABLE_MODELS)
        self._model_combo.setFixedWidth(180)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        row.addWidget(self._model_combo)

        row.addSpacing(16)

        self._status_dot = QLabel("●")
        self._status_dot.setFixedWidth(16)
        row.addWidget(self._status_dot)
        self._api_label = QLabel("Checking…")
        row.addWidget(self._api_label)

        row.addStretch()

        api_btn = QPushButton("API Settings…")
        api_btn.clicked.connect(self._open_settings)
        row.addWidget(api_btn)

        return row

    def _make_action_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self._detect_btn = QPushButton("Detect AI")
        self._detect_btn.setFixedHeight(30)
        self._detect_btn.setDefault(True)
        self._detect_btn.clicked.connect(self._start_detection)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(30)
        self._clear_btn.clicked.connect(self._clear_all)

        self._word_label = QLabel("Words: 0")
        self._word_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        row.addWidget(self._detect_btn)
        row.addWidget(self._clear_btn)
        row.addStretch()
        row.addWidget(self._word_label)
        return row

    def _make_score_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)

        row.addWidget(QLabel("AI Score:"))

        self._score_bar = QProgressBar()
        self._score_bar.setRange(0, 100)
        self._score_bar.setValue(0)
        self._score_bar.setTextVisible(False)
        self._score_bar.setFixedHeight(16)
        row.addWidget(self._score_bar, stretch=1)

        self._score_pct = QLabel("--%")
        self._score_pct.setFixedWidth(38)
        self._score_pct.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        row.addWidget(self._score_pct)

        row.addSpacing(12)

        # Colour legend
        for hex_color, name in (
            ("#e05555", "High"),
            ("#c9a010", "Medium"),
            ("#3a8f3a", "Human"),
        ):
            dot = QLabel("■")
            dot.setStyleSheet(f"color: {hex_color};")
            row.addWidget(dot)
            row.addWidget(QLabel(name))
            row.addSpacing(4)

        return row

    def _build_status_bar(self):
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    # ──────────────────────────────────────────────────────────────
    # BACKEND HOOKS — the two methods below are the main touch points
    # ──────────────────────────────────────────────────────────────

    @pyqtSlot(dict)
    def on_result(self, result: dict) -> None:
        """
        Called automatically when DetectionWorker emits result_ready.

        Expected dict shape:
            {
                "overall_score": float (0–100),
                "sentences": [
                    {"text": str, "ai_probability": float (0–100)},
                    ...
                ]
            }

        To call manually from a test / alternative backend:
            window.on_result({"overall_score": 72.5, "sentences": [...]})
        """
        score = float(result.get("overall_score", 0))
        sentences = result.get("sentences", [])

        self._score_bar.setValue(int(score))
        self._score_pct.setText(f"{score:.0f}%")
        self._score_bar.setStyleSheet(_chunk_style(score))

        if sentences:
            self._result_editor.highlight_sentences(sentences)
        else:
            self._result_editor.setPlainText(
                "No sentence data returned by the detector."
            )

        self._set_busy(False)
        self._status_bar.showMessage(
            f"Done — overall AI probability: {score:.1f}%"
        )

    @pyqtSlot(str)
    def on_error(self, message: str) -> None:
        """
        Called automatically when DetectionWorker emits error_occurred.

        To surface a custom error from your backend:
            window.on_error("Something went wrong: <details>")
        """
        self._set_busy(False)
        self._result_editor.setPlainText(f"[Error] {message}")
        self._status_bar.showMessage(f"Error: {message}")

    # ──────────────────────────────────────────────────────────────
    # Internal logic
    # ──────────────────────────────────────────────────────────────

    def _start_detection(self):
        text = self._input_editor.toPlainText().strip()
        if not text:
            self._status_bar.showMessage("Enter some text first.")
            return

        self._set_busy(True)
        self._status_bar.showMessage("Analyzing…")

        # ── BACKEND HOOK ──────────────────────────────────────────
        # DetectionWorker calls self._detector.detect(text) off the main thread.
        # Replace self._detector with your own detector instance if needed.
        self._worker = DetectionWorker(self._detector, text, parent=self)
        self._worker.result_ready.connect(self.on_result)
        self._worker.error_occurred.connect(self.on_error)
        self._worker.start()
        # ── END BACKEND HOOK ──────────────────────────────────────

    def _clear_all(self):
        self._input_editor.clear()
        self._result_editor.clear()
        self._score_bar.setValue(0)
        self._score_pct.setText("--%")
        self._score_bar.setStyleSheet("")
        self._status_bar.showMessage("Ready")

    def _open_settings(self):
        dlg = SettingsDialog(
            current_model=self._model_combo.currentText(),
            parent=self,
        )
        if dlg.exec():
            self._model_combo.setCurrentText(dlg.selected_model())
            # Re-create the detector so it picks up the new API key / model
            self._detector = Detector()
            self._refresh_api_status()

    def _on_model_changed(self, model: str):
        os.environ["GEMINI_MODEL"] = model

    def _on_text_changed(self):
        words = len(self._input_editor.toPlainText().split())
        self._word_label.setText(f"Words: {words}")

    def _set_busy(self, busy: bool):
        self._detect_btn.setEnabled(not busy)
        self._clear_btn.setEnabled(not busy)
        self._detect_btn.setText("Analyzing…" if busy else "Detect AI")

    def _refresh_api_status(self):
        has_key = bool(os.getenv("GEMINI_API_KEY"))
        if has_key:
            self._status_dot.setStyleSheet("color: green;")
            self._api_label.setText("API key loaded")
        else:
            self._status_dot.setStyleSheet("color: red;")
            self._api_label.setText("No API key — open Settings")


# ──────────────────────────────────────────────────────────────────
# Module-level helpers
# ──────────────────────────────────────────────────────────────────

def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


def _chunk_style(score: float) -> str:
    if score >= 70:
        color = "#e05555"
    elif score >= 40:
        color = "#c9a010"
    else:
        color = "#3a8f3a"
    return (
        f"QProgressBar {{ border: 1px solid #aaa; border-radius: 3px; background: #f0f0f0; }}"
        f"QProgressBar::chunk {{ background-color: {color}; border-radius: 2px; }}"
    )
