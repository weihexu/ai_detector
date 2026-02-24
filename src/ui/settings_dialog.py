import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt

# ── BACKEND HOOK ──────────────────────────────────────────────────────────
# Add or remove model IDs here as new Gemini models become available.
AVAILABLE_MODELS: list[str] = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-pro",
]
# ── END BACKEND HOOK ──────────────────────────────────────────────────────

# Project-root .env file (two levels up from src/ui/)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class SettingsDialog(QDialog):
    """
    Dialog for entering API credentials and selecting a model.
    Saves settings to the project-root .env file and updates os.environ
    so the Detector picks them up immediately when re-instantiated.
    """

    def __init__(self, current_model: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Settings")
        self.setMinimumWidth(460)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ── Info label ────────────────────────────────────────────
        info = QLabel(
            "Settings are saved to <code>.env</code> in the project root. "
            "Restart the app if the detector does not respond after saving."
        )
        info.setWordWrap(True)
        info.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(info)

        # ── Form ──────────────────────────────────────────────────
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # API Key
        key_row = QHBoxLayout()
        self._key_edit = QLineEdit()
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_edit.setPlaceholderText("Paste your Gemini API key…")
        self._key_edit.setText(os.getenv("GEMINI_API_KEY", ""))

        self._show_btn = QPushButton("Show")
        self._show_btn.setFixedWidth(54)
        self._show_btn.clicked.connect(self._toggle_visibility)

        key_row.addWidget(self._key_edit)
        key_row.addWidget(self._show_btn)
        form.addRow("API Key:", key_row)

        # Model selector
        self._model_combo = QComboBox()
        self._model_combo.addItems(AVAILABLE_MODELS)
        if current_model in AVAILABLE_MODELS:
            self._model_combo.setCurrentText(current_model)
        form.addRow("Model:", self._model_combo)

        root.addLayout(form)

        # ── Buttons ───────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    # ── Public API ────────────────────────────────────────────────
    def selected_model(self) -> str:
        return self._model_combo.currentText()

    def api_key(self) -> str:
        return self._key_edit.text().strip()

    # ── Private ───────────────────────────────────────────────────
    def _toggle_visibility(self):
        hidden = self._key_edit.echoMode() == QLineEdit.EchoMode.Password
        self._key_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if hidden else QLineEdit.EchoMode.Password
        )
        self._show_btn.setText("Hide" if hidden else "Show")

    def _save(self):
        key = self.api_key()
        model = self.selected_model()
        _upsert_env({"GEMINI_API_KEY": key, "GEMINI_MODEL": model})
        os.environ["GEMINI_API_KEY"] = key
        os.environ["GEMINI_MODEL"] = model
        self.accept()


# ── Helpers ───────────────────────────────────────────────────────────────

def _upsert_env(updates: dict[str, str]) -> None:
    """Write or update key=value pairs in the .env file."""
    lines: list[str] = (
        _ENV_FILE.read_text().splitlines() if _ENV_FILE.exists() else []
    )
    for var, val in updates.items():
        entry = f"{var}={val}"
        for i, line in enumerate(lines):
            if line.startswith(f"{var}="):
                lines[i] = entry
                break
        else:
            lines.append(entry)
    _ENV_FILE.write_text("\n".join(lines) + "\n")
