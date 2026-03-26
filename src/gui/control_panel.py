"""Control panel widget for QCM-Dual application.

Provides measurement controls: start/stop/single buttons, measurement rate
radio buttons, auto-tune check boxes, I/O mode combos, and temperature
calibration buttons.  Located in Zone 1 (top bar, right side).
"""
import logging

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
)

logger = logging.getLogger(__name__)

# I/O mode options presented in the combo boxes
IO_MODE_OPTIONS: list[str] = [
    "NC (off)",
    "Ext. input",
    "Lever out",
    "10 MHz out",
]


def _make_vsep() -> QFrame:
    """Return a thin vertical separator line for use between control groups."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Plain)
    sep.setStyleSheet("color: #3a3a5c;")
    sep.setFixedWidth(2)
    return sep


class ControlPanel(QFrame):
    """Horizontal panel with all measurement controls.

    The parent (MainWindow) is responsible for wiring each widget's signal
    to the corresponding slot on the AcquisitionEngine / SerialManager.

    Attributes:
        start_btn: QPushButton to start continuous measurement.
        stop_btn: QPushButton to stop measurement.
        single_btn: QPushButton for a single measurement.
        mode_1x: QRadioButton for 1x/s rate.
        mode_5x: QRadioButton for 5x/s rate.
        rate_group: QButtonGroup containing the two rate radios.
        tune_a_cb: QCheckBox for auto-tune channel A.
        tune_b_cb: QCheckBox for auto-tune channel B.
        io_mode_a_combo: QComboBox for I/O mode channel A.
        io_mode_b_combo: QComboBox for I/O mode channel B.
        temp_inc_a_btn: QPushButton for temperature +0.1 C channel A.
        temp_dec_a_btn: QPushButton for temperature -0.1 C channel A.
        temp_inc_b_btn: QPushButton for temperature +0.1 C channel B.
        temp_dec_b_btn: QPushButton for temperature -0.1 C channel B.
    """

    def __init__(self, parent: "QWidget | None" = None) -> None:
        super().__init__(parent)
        self._build_ui()
        logger.debug("ControlPanel initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Lay out all control groups horizontally with vertical separators."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # --- Start / Stop / Single buttons ------------------------------
        self.start_btn = QPushButton("\u25b6 Start")
        self.start_btn.setToolTip("Start continuous measurement (send A)")
        self.stop_btn = QPushButton("\u23f9 Stop")
        self.stop_btn.setToolTip("Stop measurement (send B)")
        self.single_btn = QPushButton("\u2460 Single")
        self.single_btn.setToolTip("Acquire a single measurement (send C)")

        for btn in (self.start_btn, self.stop_btn, self.single_btn):
            layout.addWidget(btn)

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
        self.tune_a_cb.setToolTip("Enable auto-tuning for channel A")
        self.tune_b_cb = QCheckBox("Tune B")
        self.tune_b_cb.setChecked(True)
        self.tune_b_cb.setToolTip("Enable auto-tuning for channel B")

        layout.addWidget(self.tune_a_cb)
        layout.addWidget(self.tune_b_cb)

        layout.addWidget(_make_vsep())

        # --- I/O mode combo boxes ---------------------------------------
        io_a_label = QLabel("I/O A:")
        io_a_label.setProperty("role", "secondary")
        layout.addWidget(io_a_label)

        self.io_mode_a_combo = QComboBox()
        self.io_mode_a_combo.addItems(IO_MODE_OPTIONS)
        self.io_mode_a_combo.setToolTip("I/O mode for channel A")
        layout.addWidget(self.io_mode_a_combo)

        io_b_label = QLabel("I/O B:")
        io_b_label.setProperty("role", "secondary")
        layout.addWidget(io_b_label)

        self.io_mode_b_combo = QComboBox()
        self.io_mode_b_combo.addItems(IO_MODE_OPTIONS)
        self.io_mode_b_combo.setToolTip("I/O mode for channel B")
        layout.addWidget(self.io_mode_b_combo)

        layout.addWidget(_make_vsep())

        # --- Temperature calibration buttons ----------------------------
        temp_label = QLabel("Temp cal:")
        temp_label.setProperty("role", "secondary")
        layout.addWidget(temp_label)

        self.temp_inc_a_btn = QPushButton("T+A")
        self.temp_inc_a_btn.setToolTip("Increase temperature offset ch A by +0.1 \u00b0C (send D)")
        self.temp_dec_a_btn = QPushButton("T\u2212A")
        self.temp_dec_a_btn.setToolTip("Decrease temperature offset ch A by \u22120.1 \u00b0C (send E)")
        self.temp_inc_b_btn = QPushButton("T+B")
        self.temp_inc_b_btn.setToolTip("Increase temperature offset ch B by +0.1 \u00b0C (send U)")
        self.temp_dec_b_btn = QPushButton("T\u2212B")
        self.temp_dec_b_btn.setToolTip("Decrease temperature offset ch B by \u22120.1 \u00b0C (send V)")

        for btn in (self.temp_inc_a_btn, self.temp_dec_a_btn,
                     self.temp_inc_b_btn, self.temp_dec_b_btn):
            btn.setFixedWidth(42)
            layout.addWidget(btn)

        layout.addStretch()

