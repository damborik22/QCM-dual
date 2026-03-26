"""Device settings dialog for QCM-Dual.

Contains DDS auto-tuning, I/O connector configuration, and temperature
calibration — settings that are rarely changed during normal operation.
"""
import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

IO_MODE_OPTIONS: list[tuple[str, str]] = [
    ("NC — disconnected", "NC"),
    ("External signal input (TTL)", "EXT"),
    ("Lever oscillator output", "LEVER"),
    ("10 MHz clock output", "10MHZ"),
]


class DeviceSettingsDialog(QDialog):
    """Dialog for I/O connector mode and temperature calibration.

    Attributes:
        io_mode_a_combo: QComboBox for I/O mode channel A (SMB connector).
        io_mode_b_combo: QComboBox for I/O mode channel B (BNC connector).
        temp_inc_a_btn: QPushButton +0.1°C channel A.
        temp_dec_a_btn: QPushButton -0.1°C channel A.
        temp_inc_b_btn: QPushButton +0.1°C channel B.
        temp_dec_b_btn: QPushButton -0.1°C channel B.
        temp_offset_a_label: QLabel showing current offset A.
        temp_offset_b_label: QLabel showing current offset B.
        tune_a_cb: QCheckBox for DDS auto-tuning channel A.
        tune_b_cb: QCheckBox for DDS auto-tuning channel B.
    """

    temp_cal_changed = Signal(str, float)  # (channel "A"/"B", new_offset)
    io_mode_changed = Signal(str, str)     # (channel "A"/"B", mode key)
    tune_changed = Signal(str, bool)       # (channel "A"/"B", enabled)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Device Settings")
        self.setMinimumWidth(420)
        self._temp_offset_a = 0.0
        self._temp_offset_b = 0.0
        self._build_ui()
        logger.debug("DeviceSettingsDialog initialized")

    def _build_ui(self) -> None:
        """Build the dialog layout."""
        layout = QVBoxLayout(self)

        # --- DDS Auto-Tuning ---
        tune_group = QGroupBox("DDS Auto-Tuning")
        tune_layout = QVBoxLayout(tune_group)

        self.tune_a_cb = QCheckBox("Channel A — auto-tune enabled (recommended)")
        self.tune_a_cb.setChecked(True)
        self.tune_a_cb.setToolTip(
            "DDS oscillator tracks the QCM sensor frequency every second.\n"
            "Recommended to keep enabled at all times."
        )
        self.tune_a_cb.toggled.connect(lambda on: self.tune_changed.emit("A", on))
        tune_layout.addWidget(self.tune_a_cb)

        self.tune_b_cb = QCheckBox("Channel B — auto-tune enabled (recommended)")
        self.tune_b_cb.setChecked(True)
        self.tune_b_cb.setToolTip(
            "DDS oscillator tracks the QCM sensor frequency every second.\n"
            "Recommended to keep enabled at all times."
        )
        self.tune_b_cb.toggled.connect(lambda on: self.tune_changed.emit("B", on))
        tune_layout.addWidget(self.tune_b_cb)

        layout.addWidget(tune_group)

        # --- I/O Connector Configuration ---
        io_group = QGroupBox("I/O Connector Configuration")
        io_layout = QFormLayout(io_group)

        self.io_mode_a_combo = QComboBox()
        for label, _key in IO_MODE_OPTIONS:
            self.io_mode_a_combo.addItem(label)
        self.io_mode_a_combo.setToolTip("Channel A — SMB connector on front panel")
        self.io_mode_a_combo.currentIndexChanged.connect(
            lambda idx: self.io_mode_changed.emit("A", IO_MODE_OPTIONS[idx][1])
        )
        io_layout.addRow("Channel A (SMB):", self.io_mode_a_combo)

        self.io_mode_b_combo = QComboBox()
        for label, _key in IO_MODE_OPTIONS:
            self.io_mode_b_combo.addItem(label)
        self.io_mode_b_combo.setToolTip("Channel B — BNC connector on front panel")
        self.io_mode_b_combo.currentIndexChanged.connect(
            lambda idx: self.io_mode_changed.emit("B", IO_MODE_OPTIONS[idx][1])
        )
        io_layout.addRow("Channel B (BNC):", self.io_mode_b_combo)

        layout.addWidget(io_group)

        # --- Temperature Calibration ---
        temp_group = QGroupBox("Temperature Calibration")
        temp_layout = QVBoxLayout(temp_group)

        # Channel A
        row_a = QHBoxLayout()
        row_a.addWidget(QLabel("Channel A:"))
        self.temp_offset_a_label = QLabel("0.0 °C")
        self.temp_offset_a_label.setMinimumWidth(80)
        row_a.addWidget(self.temp_offset_a_label)

        self.temp_dec_a_btn = QPushButton("−0.1 °C")
        self.temp_dec_a_btn.setToolTip("Decrease temperature calibration ch A (send E)")
        self.temp_dec_a_btn.clicked.connect(lambda: self._adjust_temp("A", -0.1))
        row_a.addWidget(self.temp_dec_a_btn)

        self.temp_inc_a_btn = QPushButton("+0.1 °C")
        self.temp_inc_a_btn.setToolTip("Increase temperature calibration ch A (send D)")
        self.temp_inc_a_btn.clicked.connect(lambda: self._adjust_temp("A", 0.1))
        row_a.addWidget(self.temp_inc_a_btn)

        row_a.addStretch()
        temp_layout.addLayout(row_a)

        # Channel B
        row_b = QHBoxLayout()
        row_b.addWidget(QLabel("Channel B:"))
        self.temp_offset_b_label = QLabel("0.0 °C")
        self.temp_offset_b_label.setMinimumWidth(80)
        row_b.addWidget(self.temp_offset_b_label)

        self.temp_dec_b_btn = QPushButton("−0.1 °C")
        self.temp_dec_b_btn.setToolTip("Decrease temperature calibration ch B (send V)")
        self.temp_dec_b_btn.clicked.connect(lambda: self._adjust_temp("B", -0.1))
        row_b.addWidget(self.temp_dec_b_btn)

        self.temp_inc_b_btn = QPushButton("+0.1 °C")
        self.temp_inc_b_btn.setToolTip("Increase temperature calibration ch B (send U)")
        self.temp_inc_b_btn.clicked.connect(lambda: self._adjust_temp("B", 0.1))
        row_b.addWidget(self.temp_inc_b_btn)

        row_b.addStretch()
        temp_layout.addLayout(row_b)

        layout.addWidget(temp_group)

        # --- Close button ---
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def set_temp_offsets(self, offset_a: float, offset_b: float) -> None:
        """Set the displayed temperature calibration offsets.

        Args:
            offset_a: Current offset for channel A in °C.
            offset_b: Current offset for channel B in °C.
        """
        self._temp_offset_a = offset_a
        self._temp_offset_b = offset_b
        self.temp_offset_a_label.setText(f"{offset_a:+.1f} °C")
        self.temp_offset_b_label.setText(f"{offset_b:+.1f} °C")

    def set_io_modes(self, mode_a: str, mode_b: str) -> None:
        """Set the I/O mode combo selections.

        Args:
            mode_a: Mode key for channel A ("NC", "EXT", "LEVER", "10MHZ").
            mode_b: Mode key for channel B.
        """
        keys = [k for _, k in IO_MODE_OPTIONS]
        if mode_a in keys:
            self.io_mode_a_combo.setCurrentIndex(keys.index(mode_a))
        if mode_b in keys:
            self.io_mode_b_combo.setCurrentIndex(keys.index(mode_b))

    def _adjust_temp(self, channel: str, delta: float) -> None:
        """Adjust temperature offset and emit signal.

        Args:
            channel: "A" or "B".
            delta: Amount to adjust (+0.1 or -0.1).
        """
        if channel == "A":
            self._temp_offset_a += delta
            self.temp_offset_a_label.setText(f"{self._temp_offset_a:+.1f} °C")
            self.temp_cal_changed.emit("A", self._temp_offset_a)
        else:
            self._temp_offset_b += delta
            self.temp_offset_b_label.setText(f"{self._temp_offset_b:+.1f} °C")
            self.temp_cal_changed.emit("B", self._temp_offset_b)
