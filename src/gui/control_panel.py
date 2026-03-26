"""Control panel widget for QCM-Dual application.

Provides measurement controls: start/stop/single buttons, measurement rate
radio buttons, and auto-tune check boxes.  Located in Zone 1 (top bar, right
side).  I/O mode and temperature calibration are in Device Settings dialog.
"""
import logging

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
)

logger = logging.getLogger(__name__)


def _make_vsep() -> QFrame:
    """Return a thin vertical separator line for use between control groups."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Plain)
    sep.setStyleSheet("color: #3a3a5c;")
    sep.setFixedWidth(2)
    return sep


class ControlPanel(QFrame):
    """Horizontal panel with measurement controls.

    Attributes:
        start_btn: QPushButton to start receiving data from device.
        stop_btn: QPushButton to stop receiving data.
        record_btn: QPushButton (checkable) to start/stop recording measurement.
        mode_1x: QRadioButton for 1x/s rate.
        mode_5x: QRadioButton for 5x/s rate.
        rate_group: QButtonGroup containing the two rate radios.
        ref_combo: QComboBox for reference channel selection.
    """

    def __init__(self, parent: "QWidget | None" = None) -> None:
        super().__init__(parent)
        self._build_ui()
        logger.debug("ControlPanel initialized")

    def _build_ui(self) -> None:
        """Lay out all control groups horizontally with vertical separators."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # --- Start / Stop receiving ----------------------------------------
        self.start_btn = QPushButton("\u25b6 Start")
        self.start_btn.setToolTip("Start receiving data from device")
        self.stop_btn = QPushButton("\u23f9 Stop")
        self.stop_btn.setToolTip("Stop receiving data")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        layout.addWidget(_make_vsep())

        # --- Record measurement --------------------------------------------
        self.record_btn = QPushButton("\u23fa Record")
        self.record_btn.setToolTip("Start/stop recording measurement")
        self.record_btn.setCheckable(True)
        self.record_btn.setStyleSheet(
            "QPushButton { color: #e0e0e0; }"
            "QPushButton:checked { background: #c62828; color: #ffffff; font-weight: bold; }"
        )
        layout.addWidget(self.record_btn)

        layout.addWidget(_make_vsep())

        # --- Measurement rate radio buttons -----------------------------
        self.mode_1x = QRadioButton("1\u00d7/s")
        self.mode_1x.setToolTip("Normal rate: 1 measurement per second")
        self.mode_1x.setChecked(True)
        self.mode_5x = QRadioButton("5\u00d7/s")
        self.mode_5x.setToolTip("Fast rate: 5 measurements per second")

        self.rate_group = QButtonGroup(self)
        self.rate_group.addButton(self.mode_1x, 0)
        self.rate_group.addButton(self.mode_5x, 1)

        rate_label = QLabel("Rate:")
        rate_label.setProperty("role", "secondary")
        layout.addWidget(rate_label)
        layout.addWidget(self.mode_1x)
        layout.addWidget(self.mode_5x)

        layout.addWidget(_make_vsep())

        # --- Reference channel selector -----------------------------------
        ref_label = QLabel("Reference:")
        ref_label.setProperty("role", "secondary")
        layout.addWidget(ref_label)

        self.ref_combo = QComboBox()
        self.ref_combo.addItems(["None", "Ch A", "Ch B"])
        self.ref_combo.setToolTip(
            "Select reference channel for differential measurement.\n"
            "Ch A as ref → Diff = B − A\n"
            "Ch B as ref → Diff = A − B"
        )
        layout.addWidget(self.ref_combo)

        layout.addStretch()

