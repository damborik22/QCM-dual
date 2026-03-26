"""Application controller wiring all components together.

Connects SerialManager, AcquisitionEngine, and GUI panels via
Qt Signals/Slots. Owns the core objects and manages application state.
"""
import logging
import time
from collections import deque
from pathlib import Path

import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog

from src.core.acquisition import AcquisitionEngine
from src.core.data_models import MeasurementPoint
from src.core.method import Method, load_method, save_method
from src.core.serial_manager import SerialManager
from src.gui.device_settings_dialog import DeviceSettingsDialog
from src.gui.main_window import MainWindow

logger = logging.getLogger(__name__)


class AppController:
    """Wires all application components together.

    Owns SerialManager, AcquisitionEngine, and connects them to the
    MainWindow's GUI panels.
    """

    def __init__(self, window: MainWindow) -> None:
        self.window = window
        self.serial_manager = SerialManager()
        self.engine = AcquisitionEngine(self.serial_manager)
        self.method = Method()

        self._start_time: float | None = None
        self._point_count = 0
        self._error_count = 0
        self._tared = False
        self._ref_channel: str = "None"

        # Plot data buffers (parallel arrays for performance)
        self._plot_times: deque[float] = deque(maxlen=86400)
        self._plot_data: dict[str, deque[float]] = {
            "freq_a": deque(maxlen=86400),
            "freq_b": deque(maxlen=86400),
            "delta_f_diff": deque(maxlen=86400),
            "delta_m_diff": deque(maxlen=86400),
            "temp_a": deque(maxlen=86400),
            "temp_b": deque(maxlen=86400),
        }

        # Elapsed time timer
        self._elapsed_timer = QTimer()
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._update_elapsed)

        # Device settings dialog (lazy)
        self._device_settings: DeviceSettingsDialog | None = None

        self._connect_signals()
        self._update_port_list()
        logger.info("AppController initialized")

    def _connect_signals(self) -> None:
        """Wire all signals/slots between components."""
        w = self.window

        # Connection panel
        w.connection_panel.connect_btn.clicked.connect(self._on_connect_clicked)
        self.serial_manager.connection_changed.connect(self._on_connection_changed)
        self.serial_manager.error_occurred.connect(self._on_error)

        # Control panel
        w.control_panel.start_btn.clicked.connect(self._on_start)
        w.control_panel.stop_btn.clicked.connect(self._on_stop)
        w.control_panel.mode_1x.toggled.connect(
            lambda checked: self._on_mode_changed(fast=False) if checked else None
        )
        w.control_panel.mode_5x.toggled.connect(
            lambda checked: self._on_mode_changed(fast=True) if checked else None
        )
        w.control_panel.ref_combo.currentTextChanged.connect(self._on_ref_changed)

        # Acquisition engine
        self.engine.new_point.connect(self._on_new_point)

        # Plot panel
        w.plot_panel.tare_requested.connect(self._on_tare)
        w.plot_panel.clear_requested.connect(self._on_clear)

        # Menu actions
        w.action_new_method.triggered.connect(self._on_new_method)
        w.action_open_method.triggered.connect(self._on_open_method)
        w.action_save_method.triggered.connect(self._on_save_method)
        w.action_save_method_as.triggered.connect(self._on_save_method_as)
        w.action_device_settings.triggered.connect(self._on_device_settings)

    def _update_port_list(self) -> None:
        """Refresh available ports in the connection panel."""
        ports = self.serial_manager.get_available_ports()
        self.window.connection_panel.set_ports(ports)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _on_connect_clicked(self) -> None:
        """Toggle connection based on current state."""
        if self.serial_manager.is_connected():
            self.serial_manager.disconnect()
        else:
            port = self.window.connection_panel.port_combo.currentText()
            self.serial_manager.connect(port)

    def _on_connection_changed(self, connected: bool) -> None:
        """Update GUI when connection state changes."""
        self.window.connection_panel.set_connected(connected)
        if connected:
            port = self.window.connection_panel.port_combo.currentText()
            self.window.connection_label.setText(port)
        else:
            self.window.connection_label.setText("Disconnected")

    def _on_error(self, message: str) -> None:
        """Handle error from serial manager."""
        self._error_count += 1
        self.window.errors_label.setText(f"Errors: {self._error_count}")
        logger.error("Serial error: %s", message)

    # ------------------------------------------------------------------
    # Start / Stop / Mode
    # ------------------------------------------------------------------

    def _on_start(self) -> None:
        """Start continuous acquisition."""
        if not self.serial_manager.is_connected():
            logger.warning("Cannot start: not connected")
            return
        self._start_time = time.time()
        self._elapsed_timer.start()
        self.engine.start()

    def _on_stop(self) -> None:
        """Stop acquisition."""
        self._elapsed_timer.stop()
        self.engine.stop()

    def _on_mode_changed(self, fast: bool) -> None:
        """Switch measurement rate."""
        self.engine.set_mode(fast=fast)
        self.window.mode_label.setText("5\u00d7/s" if fast else "1\u00d7/s")

    # ------------------------------------------------------------------
    # Data handling
    # ------------------------------------------------------------------

    def _on_new_point(self, point: MeasurementPoint) -> None:
        """Process a new measurement point: update display, plot, status."""
        self._point_count += 1

        # Compute display values (frequency becomes tared if tare is set)
        freq_a_display = point.delta_f_a if self._tared else point.freq_a
        freq_b_display = point.delta_f_b if self._tared else point.freq_b

        # Update display cards
        self.window.display_panel.card_a.update_values({
            "freq": self._fmt_freq(freq_a_display, self._tared),
            "temp": self._fmt_temp(point.temp_a),
        })
        self.window.display_panel.card_b.update_values({
            "freq": self._fmt_freq(freq_b_display, self._tared),
            "temp": self._fmt_temp(point.temp_b),
        })

        # Differential
        if self._ref_channel != "None" and self._tared:
            if self._ref_channel == "Ch A":
                delta_f = point.delta_f_b - point.delta_f_a
            else:
                delta_f = point.delta_f_a - point.delta_f_b
            delta_m = 0.0  # Sauerbrey in Phase 5
            self.window.display_panel.card_diff.update_values({
                "delta_f": f"{delta_f:+.3f} Hz",
                "delta_m": f"{delta_m:+.3f} ng/cm\u00b2",
            })
        else:
            delta_f = 0.0
            delta_m = 0.0

        # Plot data
        elapsed = point.timestamp - (self._start_time or point.timestamp)
        self._plot_times.append(elapsed)
        self._plot_data["freq_a"].append(freq_a_display)
        self._plot_data["freq_b"].append(freq_b_display)
        self._plot_data["delta_f_diff"].append(delta_f)
        self._plot_data["delta_m_diff"].append(delta_m)
        self._plot_data["temp_a"].append(point.temp_a)
        self._plot_data["temp_b"].append(point.temp_b)

        self._update_plot()

        # Status bar
        self.window.points_label.setText(f"Points: {self._point_count}")
        self.window.voltage_label.setText(f"Ux: {point.voltage_ux:.5f} V")

    def _update_plot(self) -> None:
        """Push buffered data to visible plot traces."""
        times = np.array(self._plot_times)
        if len(times) == 0:
            return

        pp = self.window.plot_panel
        for key, buf in self._plot_data.items():
            if key in pp.traces and pp.toggle_buttons.get(key, None) is not None:
                if pp.toggle_buttons[key].isChecked():
                    pp.traces[key].setData(times, np.array(buf))

    def _update_elapsed(self) -> None:
        """Update elapsed time in status bar."""
        if self._start_time is None:
            return
        elapsed = int(time.time() - self._start_time)
        h, remainder = divmod(elapsed, 3600)
        m, s = divmod(remainder, 60)
        self.window.elapsed_label.setText(f"\u23f1 {h:02d}:{m:02d}:{s:02d}")

    # ------------------------------------------------------------------
    # Tare / Clear
    # ------------------------------------------------------------------

    def _on_tare(self) -> None:
        """Tare both channels and switch plot to diff view."""
        self.engine.tare("both")
        self._tared = True
        # Auto-switch plot to differential if reference is set
        if self._ref_channel != "None":
            self.window.plot_panel.switch_to_diff()
        logger.info("Tare applied")

    def _on_clear(self) -> None:
        """Clear all data buffers and reset display."""
        # TODO Phase 5: auto-save + confirmation dialog
        self.engine.clear_buffer()
        self._plot_times.clear()
        for buf in self._plot_data.values():
            buf.clear()
        self._point_count = 0
        self._tared = False
        self._start_time = None

        # Reset plot traces
        for trace in self.window.plot_panel.traces.values():
            trace.setData([], [])

        # Reset display cards
        self.window.display_panel.card_a.reset()
        self.window.display_panel.card_b.reset()
        self.window.display_panel.card_diff.reset()

        # Reset status bar
        self.window.elapsed_label.setText("\u23f1 00:00:00")
        self.window.points_label.setText("Points: 0")
        self.window.voltage_label.setText("Ux: 0.00000 V")

        # Switch plot back to frequency view
        self.window.plot_panel.switch_to_freq()
        logger.info("Data cleared")

    # ------------------------------------------------------------------
    # Reference channel
    # ------------------------------------------------------------------

    def _on_ref_changed(self, ref: str) -> None:
        """Handle reference channel change."""
        self._ref_channel = ref

    # ------------------------------------------------------------------
    # Method file I/O
    # ------------------------------------------------------------------

    def _on_new_method(self) -> None:
        """Reset to default method."""
        self.method = Method()
        self._apply_method()
        self._on_clear()
        self.window.setWindowTitle("QCM-Dual — Untitled")

    def _on_open_method(self) -> None:
        """Open a .qcm method file."""
        path, _ = QFileDialog.getOpenFileName(
            self.window, "Open Method", "", "QCM Methods (*.qcm);;All Files (*)"
        )
        if not path:
            return
        try:
            self.method = load_method(Path(path))
            self._apply_method()
            self.window.setWindowTitle(f"QCM-Dual \u2014 {self.method.name}")
        except Exception as exc:
            logger.error("Failed to load method: %s", exc)

    def _on_save_method(self) -> None:
        """Save method (save-as if no path yet)."""
        self._on_save_method_as()

    def _on_save_method_as(self) -> None:
        """Save method to a new .qcm file."""
        path, _ = QFileDialog.getSaveFileName(
            self.window, "Save Method", f"{self.method.name}.qcm",
            "QCM Methods (*.qcm);;All Files (*)"
        )
        if not path:
            return
        self._collect_method_from_gui()
        try:
            save_method(self.method, Path(path))
            self.window.setWindowTitle(f"QCM-Dual \u2014 {self.method.name}")
        except Exception as exc:
            logger.error("Failed to save method: %s", exc)

    def _apply_method(self) -> None:
        """Apply loaded method settings to the GUI."""
        w = self.window
        w.control_panel.mode_5x.setChecked(self.method.mode_fast)
        w.control_panel.mode_1x.setChecked(not self.method.mode_fast)

    def _collect_method_from_gui(self) -> None:
        """Read current GUI state into self.method."""
        w = self.window
        self.method.mode_fast = w.control_panel.mode_5x.isChecked()

    # ------------------------------------------------------------------
    # Device settings dialog
    # ------------------------------------------------------------------

    def _on_device_settings(self) -> None:
        """Open the device settings dialog."""
        if self._device_settings is None:
            self._device_settings = DeviceSettingsDialog(self.window)
            self._device_settings.io_mode_changed.connect(self._on_io_mode_changed)
            self._device_settings.temp_cal_changed.connect(self._on_temp_cal_changed)
            self._device_settings.tune_changed.connect(self._on_tune_changed)
        self._device_settings.exec()

    def _on_io_mode_changed(self, channel: str, mode: str) -> None:
        """Send I/O mode command to device."""
        cmd_map_a = {"NC": "K", "EXT": "J", "LEVER": "L", "10MHZ": "M"}
        cmd_map_b = {"NC": "P", "EXT": "O", "LEVER": "Q", "10MHZ": "R"}
        cmd_map = cmd_map_a if channel == "A" else cmd_map_b
        cmd = cmd_map.get(mode)
        if cmd:
            self.serial_manager.send_command(cmd)
            logger.info("I/O mode %s ch %s → command %s", mode, channel, cmd)

    def _on_temp_cal_changed(self, channel: str, offset: float) -> None:
        """Send temperature calibration command."""
        # The signal gives us the total offset; we just need to send
        # the last D/E/U/V that was pressed. The dialog handles +/- internally.
        logger.info("Temp cal ch %s offset: %+.1f°C", channel, offset)

    def _on_tune_changed(self, channel: str, enabled: bool) -> None:
        """Send DDS tuning command."""
        if channel == "A":
            self.serial_manager.send_command("H" if enabled else "I")
        else:
            self.serial_manager.send_command("S" if enabled else "T")
        logger.info("Tune ch %s: %s", channel, "enabled" if enabled else "disabled")

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_freq(value: float, tared: bool) -> str:
        """Format frequency for display.

        Before tare: '9 979 521.207 Hz' (space-separated thousands).
        After tare: '+12.350 Hz' (signed, relative).
        """
        if tared:
            return f"{value:+.3f} Hz"
        return f"{value:,.3f} Hz".replace(",", " ")

    @staticmethod
    def _fmt_temp(value: float) -> str:
        """Format temperature for display."""
        if abs(value - 99.9) < 0.05:
            return "---"
        return f"{value:.1f} \u00b0C"
