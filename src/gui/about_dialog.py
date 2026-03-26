"""About dialog for QCM-Dual application.

Displays application name, version, description, manufacturer info,
and technology stack in a simple informational dialog.
"""
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class AboutDialog(QDialog):
    """Simple About dialog showing application and manufacturer info.

    Styled with dark theme colors consistent with the rest of the
    application. Closed via a single OK button.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About QCM-Dual")
        self.setFixedWidth(420)
        self._build_ui()
        logger.debug("AboutDialog initialized")

    def _build_ui(self) -> None:
        """Build the dialog layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Application name
        name_label = QLabel("QCM-Dual Control Software")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setObjectName("aboutAppName")
        layout.addWidget(name_label)

        # Version
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setObjectName("aboutVersion")
        layout.addWidget(version_label)

        # Separator
        layout.addSpacing(8)

        # Description
        description_label = QLabel(
            "Desktop application for the QCM-Dual frequency meter.\n"
            "Dual-channel quartz crystal microbalance control,\n"
            "data acquisition, and real-time visualization."
        )
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setObjectName("aboutDescription")
        layout.addWidget(description_label)

        layout.addSpacing(8)

        # Manufacturer
        manufacturer_label = QLabel(
            "Device: KEVA\n"
            "Ing. Pavel Krasensky\n"
            "Vinohrady 90, Brno\n"
            "p.krasen@gmail.com"
        )
        manufacturer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        manufacturer_label.setObjectName("aboutManufacturer")
        layout.addWidget(manufacturer_label)

        layout.addSpacing(8)

        # Built with
        tech_label = QLabel("Built with Python / PySide6 / pyqtgraph")
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_label.setObjectName("aboutTech")
        layout.addWidget(tech_label)

        layout.addSpacing(4)

        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
