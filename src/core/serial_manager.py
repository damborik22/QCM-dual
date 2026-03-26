"""Serial port manager for QCM-Dual.

Handles all serial I/O in a background QThread.
Provides a simulator backend for hardware-free operation.
"""
import logging
import threading
import time

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.core.simulator import QCMSimulator

logger = logging.getLogger(__name__)


class SimulatorPort:
    """Fake serial port backed by QCMSimulator.

    Mimics the pyserial Serial interface (readline, write, close).
    """

    def __init__(self) -> None:
        self._simulator = QCMSimulator()
        self._running = False
        self._last_command = "A"
        self._continuous = False
        self._single_pending = False
        self._lock = threading.Lock()

    def open(self) -> None:
        self._running = True

    def close(self) -> None:
        self._running = False

    @property
    def is_open(self) -> bool:
        return self._running

    def write(self, data: bytes) -> None:
        """Process a single-character command.

        Args:
            data: Command byte(s), e.g. b'A'.
        """
        cmd = data.decode("ascii").strip()
        if not cmd:
            return
        with self._lock:
            self._last_command = cmd
            self._simulator.process_command(cmd)
            if cmd == "A":
                self._continuous = True
            elif cmd == "B":
                self._continuous = False
            elif cmd == "C":
                self._continuous = False
                self._single_pending = True

    def readline(self) -> bytes:
        """Return next data line, blocking until available.

        Returns:
            Encoded line with CR LF, or empty bytes if port closed.
        """
        while self._running:
            with self._lock:
                should_send = self._continuous or self._single_pending
                if self._single_pending:
                    self._single_pending = False

            if should_send:
                # Simulate real device timing
                if self._continuous:
                    interval = 0.2 if self._simulator._fast_mode else 1.0
                    time.sleep(interval)
                if self._simulator._fast_mode:
                    line = self._simulator.generate_long_packet()
                else:
                    line = self._simulator.generate_short_packet()
                return (line + "\r\n").encode("ascii")

            time.sleep(0.1)
        return b""


class _ReadThread(QThread):
    """Background thread that reads lines from a serial port."""

    line_received = Signal(str)
    error = Signal(str)
    disconnected = Signal()

    def __init__(self, port: object, is_real_port: bool = False) -> None:
        super().__init__()
        self._port = port
        self._stop_flag = False
        self._is_real_port = is_real_port
        self._empty_read_count = 0

    def run(self) -> None:
        """Read lines from serial port until stopped or disconnected."""
        logger.info("Read thread started")
        while not self._stop_flag:
            try:
                raw = self._port.readline()
                if not raw:
                    if self._stop_flag:
                        break
                    # For real serial ports, consecutive empty reads
                    # indicate the device has been disconnected.
                    if self._is_real_port:
                        self._empty_read_count += 1
                        if self._empty_read_count >= 10:
                            logger.warning("Device appears disconnected "
                                           "(repeated empty reads)")
                            self.error.emit("Device disconnected")
                            self.disconnected.emit()
                            break
                    time.sleep(0.05)
                    continue
                self._empty_read_count = 0
                line = raw.decode("ascii", errors="replace").rstrip("\r\n")
                if line:
                    self.line_received.emit(line)
            except Exception as exc:
                if not self._stop_flag:
                    logger.error("Read error: %s", exc)
                    self.error.emit(str(exc))
                    self.disconnected.emit()
                break
        logger.info("Read thread stopped")

    def request_stop(self) -> None:
        self._stop_flag = True


class SerialManager(QObject):
    """Manages serial communication with the QCM-Dual device.

    All serial I/O runs in a background QThread. Communication
    with the GUI is through Qt signals only.
    """

    data_received = Signal(str)
    connection_changed = Signal(bool)
    error_occurred = Signal(str)

    _MAX_RECONNECT_RETRIES = 30
    _RECONNECT_INTERVAL_MS = 2000

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._port: object | None = None
        self._thread: _ReadThread | None = None
        self._connected = False
        self._is_simulator = False
        self._last_port: str | None = None
        self._reconnect_count = 0

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(self._RECONNECT_INTERVAL_MS)
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)

    def get_available_ports(self) -> list[str]:
        """Return list of available COM ports plus 'SIMULATOR'.

        Returns:
            List of port name strings.
        """
        ports = ["SIMULATOR"]
        try:
            import serial.tools.list_ports
            for info in serial.tools.list_ports.comports():
                ports.append(info.device)
        except ImportError:
            logger.debug("pyserial not available for port enumeration")
        return ports

    def connect(self, port: str) -> bool:
        """Connect to the specified port.

        Args:
            port: Port name, or 'SIMULATOR' for built-in simulator.

        Returns:
            True if connection succeeded.
        """
        if self._connected:
            self.disconnect()

        # Stop any pending reconnect attempts
        self._reconnect_timer.stop()
        self._reconnect_count = 0

        self._is_simulator = (port == "SIMULATOR")
        self._last_port = port

        try:
            if self._is_simulator:
                self._port = SimulatorPort()
                self._port.open()
            else:
                import serial
                self._port = serial.Serial(
                    port=port,
                    baudrate=38400,
                    bytesize=8,
                    parity="N",
                    stopbits=1,
                    timeout=1.0,
                )
        except Exception as exc:
            logger.error("Connection failed: %s", exc)
            self.error_occurred.emit(f"Connection failed: {exc}")
            return False

        self._thread = _ReadThread(self._port, is_real_port=not self._is_simulator)
        self._thread.line_received.connect(self.data_received)
        self._thread.error.connect(self.error_occurred)
        self._thread.disconnected.connect(self._on_disconnected)
        self._thread.start()

        self._connected = True
        self.connection_changed.emit(True)
        logger.info("Connected to %s", port)
        return True

    def disconnect(self) -> None:
        """Disconnect from the current port.

        Stops the read thread, closes the serial port, and cancels
        any pending reconnection attempts.
        """
        # Cancel any active reconnection attempts
        self._reconnect_timer.stop()
        self._reconnect_count = 0

        if self._thread is not None:
            self._thread.request_stop()
            if self._port is not None:
                try:
                    self._port.close()
                except Exception as exc:
                    logger.debug("Error closing port during disconnect: %s", exc)
            self._thread.wait(3000)
            self._thread = None

        if self._port is not None:
            try:
                if hasattr(self._port, "is_open") and self._port.is_open:
                    self._port.close()
            except Exception as exc:
                logger.debug("Error closing port: %s", exc)
            self._port = None

        was_connected = self._connected
        self._connected = False
        if was_connected:
            self.connection_changed.emit(False)
            logger.info("Disconnected")

    def send_command(self, cmd: str) -> None:
        """Send a single-character command to the device.

        Args:
            cmd: Single character command (A-V).
        """
        if self._port is None or not self._connected:
            logger.warning("Cannot send command: not connected")
            return
        try:
            self._port.write(cmd.encode("ascii"))
            logger.debug("Sent command: %s", cmd)
        except Exception as exc:
            logger.error("Send command failed: %s", exc)
            self.error_occurred.emit(f"Send failed: {exc}")
            # If write fails on a real port, treat as disconnect
            if not self._is_simulator:
                self._on_disconnected()

    def is_connected(self) -> bool:
        """Return current connection state."""
        return self._connected

    def _on_disconnected(self) -> None:
        """Handle unexpected disconnection from read thread.

        For real serial ports, starts a reconnection timer that attempts
        to reconnect every 2 seconds up to 30 times. For the simulator,
        simply marks as disconnected with no reconnection attempt.
        """
        if not self._connected:
            return
        self._connected = False
        self.connection_changed.emit(False)
        logger.warning("Unexpected disconnection detected")

        # Clean up the stale port/thread without re-emitting signals
        if self._thread is not None:
            self._thread.request_stop()
            # Don't wait here — we may be called from the thread itself
            self._thread = None

        if self._port is not None:
            try:
                if hasattr(self._port, "is_open") and self._port.is_open:
                    self._port.close()
            except Exception as exc:
                logger.debug("Error closing port after disconnect: %s", exc)
            self._port = None

        # Start reconnection for real serial ports only
        if not self._is_simulator and self._last_port:
            self._reconnect_count = 0
            logger.info("Starting reconnection attempts to %s", self._last_port)
            self._reconnect_timer.start()

    def _attempt_reconnect(self) -> None:
        """Try to reconnect to the last known serial port.

        Called by the reconnect timer. Gives up after max retries.
        """
        self._reconnect_count += 1
        logger.info("Reconnection attempt %d/%d to %s",
                     self._reconnect_count, self._MAX_RECONNECT_RETRIES,
                     self._last_port)

        if self._reconnect_count > self._MAX_RECONNECT_RETRIES:
            self._reconnect_timer.stop()
            logger.error("Reconnection failed after %d attempts",
                         self._MAX_RECONNECT_RETRIES)
            self.error_occurred.emit(
                f"Reconnection failed after {self._MAX_RECONNECT_RETRIES} "
                f"attempts to {self._last_port}"
            )
            return

        try:
            import serial
            port_obj = serial.Serial(
                port=self._last_port,
                baudrate=38400,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=1.0,
            )
        except Exception as exc:
            logger.debug("Reconnect attempt %d failed: %s",
                         self._reconnect_count, exc)
            return

        # Successfully opened the port — stop timer and resume
        self._reconnect_timer.stop()
        self._port = port_obj

        self._thread = _ReadThread(self._port, is_real_port=True)
        self._thread.line_received.connect(self.data_received)
        self._thread.error.connect(self.error_occurred)
        self._thread.disconnected.connect(self._on_disconnected)
        self._thread.start()

        self._connected = True
        self._reconnect_count = 0
        self.connection_changed.emit(True)
        logger.info("Reconnected to %s", self._last_port)
