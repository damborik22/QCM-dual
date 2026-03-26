"""Serial port manager for QCM-Dual.

Handles all serial I/O in a background QThread.
Provides a simulator backend for hardware-free operation.
"""
import logging
import threading
import time

from PySide6.QtCore import QObject, QThread, Signal

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

    def __init__(self, port: object) -> None:
        super().__init__()
        self._port = port
        self._stop_flag = False

    def run(self) -> None:
        logger.info("Read thread started")
        while not self._stop_flag:
            try:
                raw = self._port.readline()
                if not raw:
                    if self._stop_flag:
                        break
                    time.sleep(0.05)
                    continue
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

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._port: object | None = None
        self._thread: _ReadThread | None = None
        self._connected = False

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

        try:
            if port == "SIMULATOR":
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

        self._thread = _ReadThread(self._port)
        self._thread.line_received.connect(self.data_received)
        self._thread.error.connect(self.error_occurred)
        self._thread.disconnected.connect(self._on_disconnected)
        self._thread.start()

        self._connected = True
        self.connection_changed.emit(True)
        logger.info("Connected to %s", port)
        return True

    def disconnect(self) -> None:
        """Disconnect from the current port."""
        if self._thread is not None:
            self._thread.request_stop()
            if self._port is not None:
                self._port.close()
            self._thread.wait(3000)
            self._thread = None

        if self._port is not None:
            try:
                if hasattr(self._port, "is_open") and self._port.is_open:
                    self._port.close()
            except Exception:
                pass
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

    def is_connected(self) -> bool:
        """Return current connection state."""
        return self._connected

    def _on_disconnected(self) -> None:
        """Handle unexpected disconnection from read thread."""
        self._connected = False
        self.connection_changed.emit(False)
