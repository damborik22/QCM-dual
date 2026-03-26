"""Control panel widget for QCM-Dual application.

Provides measurement controls: start/stop/single buttons, measurement rate
radio buttons, and auto-tune check boxes.  Located in Zone 1 (top bar, right
side).  I/O mode and temperature calibration are in Device Settings dialog.
"""
import logging

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
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
        start_btn: QPushButton to start continuous measurement.
        stop_btn: QPushButton to stop measurement.
        mode_1x: QRadioButton for 1x/s rate.
        mode_5x: QRadioButton for 5x/s rate.
        rate_group: QButtonGroup containing the two rate radios.
        tune_a_cb: QCheckBox for auto-tune channel A.
        tune_b_cb: QCheckBox for auto-tune channel B.
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

        # --- Start / Stop buttons ----------------------------------------
        self.start_btn = QPushButton("\u25b6 Start")
        self.start_btn.setToolTip("Start continuous measurement")
        self.stop_btn = QPushButton("\u23f9 Stop")
        self.stop_btn.setToolTip("Stop measurement")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

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

        # --- Auto-tune check boxes --------------------------------------
        self.tune_a_cb = QCheckBox("Tune A")
        self.tune_a_cb.setChecked(True)
        self.tune_a_cb.setToolTip("Enable DDS auto-tuning for channel A")
        self.tune_b_cb = QCheckBox("Tune B")
        self.tune_b_cb.setChecked(True)
        self.tune_b_cb.setToolTip("Enable DDS auto-tuning for channel B")

        layout.addWidget(self.tune_a_cb)
        layout.addWidget(self.tune_b_cb)

        layout.addStretch()

