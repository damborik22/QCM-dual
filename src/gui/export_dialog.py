"""Export dialog for QCM-Dual.

Lets the user set experiment name, output folder, and choose which
recordings to export before saving CSV files.
"""
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config import get_value, set_value

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """Dialog for configuring CSV export.

    Attributes:
        experiment_name: The entered experiment name.
        output_folder: The selected output folder path.
        selected_recordings: List of recording indices (0-based) to export.
    """

    def __init__(
        self,
        recording_count: int,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the export dialog.

        Args:
            recording_count: Number of available recordings.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Export Data")
        self.setMinimumWidth(450)
        self._recording_count = recording_count
        self._checkboxes: list[QCheckBox] = []

        self.experiment_name: str = ""
        self.output_folder: str = ""
        self.selected_recordings: list[int] = []

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # --- Experiment name ---
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Test01")
        form.addRow("Experiment name:", self._name_edit)
        layout.addLayout(form)

        # --- Output folder ---
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        last_dir = get_value("export/last_directory")
        if last_dir:
            self._folder_edit.setText(str(last_dir))
        else:
            self._folder_edit.setText(str(Path.home()))
        self._folder_edit.setReadOnly(True)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(QLabel("Output folder:"))
        folder_row.addWidget(self._folder_edit, stretch=1)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        # --- Recording selection ---
        if self._recording_count > 0:
            rec_group = QGroupBox(f"Recordings ({self._recording_count} available)")
            rec_layout = QVBoxLayout(rec_group)

            select_all = QCheckBox("Select all")
            select_all.setChecked(True)
            select_all.toggled.connect(self._on_select_all)
            rec_layout.addWidget(select_all)

            for i in range(self._recording_count):
                cb = QCheckBox(f"Recording {i + 1}")
                cb.setChecked(True)
                self._checkboxes.append(cb)
                rec_layout.addWidget(cb)

            layout.addWidget(rec_group)
        else:
            layout.addWidget(QLabel("No recordings — will export entire buffer."))

        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        export_btn = QPushButton("Export")
        export_btn.setDefault(True)
        export_btn.clicked.connect(self._on_export)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(export_btn)
        layout.addLayout(btn_row)

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._folder_edit.text()
        )
        if folder:
            self._folder_edit.setText(folder)

    def _on_select_all(self, checked: bool) -> None:
        for cb in self._checkboxes:
            cb.setChecked(checked)

    def _on_export(self) -> None:
        self.experiment_name = self._name_edit.text().strip() or "Untitled"
        self.output_folder = self._folder_edit.text()
        self.selected_recordings = [
            i for i, cb in enumerate(self._checkboxes) if cb.isChecked()
        ]
        # Remember folder
        set_value("export/last_directory", self.output_folder)
        self.accept()
