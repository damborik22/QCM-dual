"""Connection panel widget for QCM-Dual application.

Provides serial port selection, connect/disconnect button, and a colored
status LED indicator.  Located in Zone 1 (top bar, left side).
"""
import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from src.gui.styles import COLOR_GREEN

logger = logging.getLogger(__name__)


class ConnectionPanel(QFrame):
    """Horizontal panel with port combo, connect button, and status LED.

    The parent (MainWindow) is responsible for connecting the button's
    ``clicked`` signal and the combo's ``currentTextChanged`` signal to
    the appropriate slots on the SerialManager.

    Attributes:
        port_combo: QComboBox listing available serial ports and SIMULATOR.
        connect_btn: QPushButton that toggles between Connect / Disconnect.
        status_led: QLabel rendered as a colored circle (green / red).
    """

    # LED diameter in pixels
    _LED_SIZE: int = 16

    def __init__(self, parent: "QWidget | None" = None) -> None:
        super().__init__(parent)
        self._connected = False
        self._build_ui()
        logger.debug("ConnectionPanel initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create child widgets and lay them out horizontally."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # --- Port label -------------------------------------------------
        port_label = QLabel("Port:")
        port_label.setProperty("role", "secondary")
        layout.addWidget(port_label)

        # --- Port combo box ---------------------------------------------
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(160)
        self.port_combo.setToolTip("Select serial port or SIMULATOR")
        self.port_combo.addItem("SIMULATOR")
        layout.addWidget(self.port_combo)

        # --- Connect / Disconnect button --------------------------------
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumWidth(100)
        self.connect_btn.setToolTip("Connect to the selected port")
        layout.addWidget(self.connect_btn)

        # --- Status LED (colored dot) -----------------------------------
        self.status_led = QLabel()
        self.status_led.setFixedSize(self._LED_SIZE, self._LED_SIZE)
        self.status_led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_led_color(connected=False)
        layout.addWidget(self.status_led)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_ports(self, ports: list[str]) -> None:
        """Populate the port combo box.

        Always ensures ``SIMULATOR`` is the first entry.  Preserves the
        current selection when possible.

        Args:
            ports: List of serial port names (e.g. ``["COM3", "COM4"]``).
        """
        current = self.port_combo.currentText()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        self.port_combo.addItem("SIMULATOR")
        for port in ports:
            if port != "SIMULATOR":
                self.port_combo.addItem(port)
        # Restore previous selection if still available
        idx = self.port_combo.findText(current)
        if idx >= 0:
            self.port_combo.setCurrentIndex(idx)
        self.port_combo.blockSignals(False)
        logger.debug("Port list updated: %s", [self.port_combo.itemText(i)
                      for i in range(self.port_combo.count())])

    def set_connected(self, connected: bool) -> None:
        """Update button text and LED color to reflect connection state.

        Args:
            connected: ``True`` when device is connected.
        """
        self._connected = connected
        if connected:
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setToolTip("Disconnect from the device")
            self.port_combo.setEnabled(False)
        else:
            self.connect_btn.setText("Connect")
            self.connect_btn.setToolTip("Connect to the selected port")
            self.port_combo.setEnabled(True)
        self._apply_led_color(connected)
        logger.debug("Connection state set to %s", connected)

    def is_connected(self) -> bool:
        """Return the current connection state shown by this panel."""
        return self._connected

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_led_color(self, connected: bool) -> None:
        """Set the LED label's stylesheet to show a colored circle.

        Args:
            connected: ``True`` for green, ``False`` for red.
        """
        color = COLOR_GREEN if connected else "#ef5350"
        self.status_led.setStyleSheet(
            f"background-color: {color};"
            f"border-radius: {self._LED_SIZE // 2}px;"
            "border: none;"
        )
