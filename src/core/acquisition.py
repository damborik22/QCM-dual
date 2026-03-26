"""Acquisition engine for QCM-Dual.

Receives raw data lines from SerialManager, parses them into
MeasurementPoints, and manages the data buffer and tare references.
"""
import logging
from collections import deque

from PySide6.QtCore import QObject, Signal

from src.core.data_models import MeasurementPoint, ShortPacket, LongPacket
from src.core.protocol import parse_line
from src.core.serial_manager import SerialManager

logger = logging.getLogger(__name__)

BUFFER_MAXLEN = 86400  # 24h at 1/sec


class AcquisitionEngine(QObject):
    """Processes incoming QCM data and manages measurement state."""

    new_point = Signal(object)
    status_changed = Signal(str)

    def __init__(
        self, serial_manager: SerialManager, parent: QObject | None = None
    ) -> None:
        """Initialize the acquisition engine.

        Args:
            serial_manager: SerialManager instance for sending commands.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self._serial = serial_manager
        self._serial.data_received.connect(self._on_data_received)

        self._buffer: deque[MeasurementPoint] = deque(maxlen=BUFFER_MAXLEN)
        self._tare_a: float | None = None
        self._tare_b: float | None = None
        self._running = False

    def start(self) -> None:
        """Start continuous acquisition (sends 'A' command)."""
        self._running = True
        self._serial.send_command("A")
        self.status_changed.emit("running")

    def stop(self) -> None:
        """Stop acquisition (sends 'B' command)."""
        self._running = False
        self._serial.send_command("B")
        self.status_changed.emit("stopped")

    def single(self) -> None:
        """Request a single measurement (sends 'C' command)."""
        self._serial.send_command("C")

    def set_mode(self, fast: bool) -> None:
        """Switch measurement rate.

        Args:
            fast: True for 5×/s (G command), False for 1×/s (F command).
        """
        self._serial.send_command("G" if fast else "F")

    def tare(self, channel: str) -> None:
        """Set tare reference to current frequency.

        Args:
            channel: 'A', 'B', or 'both'.
        """
        if not self._buffer:
            logger.warning("Cannot tare: no data in buffer")
            return
        last = self._buffer[-1]
        if channel in ("A", "both"):
            self._tare_a = last.freq_a
            logger.info("Tare A set to %.3f Hz", self._tare_a)
        if channel in ("B", "both"):
            self._tare_b = last.freq_b
            logger.info("Tare B set to %.3f Hz", self._tare_b)

    def get_buffer(self) -> list[MeasurementPoint]:
        """Return a copy of the measurement buffer.

        Returns:
            List of MeasurementPoint objects.
        """
        return list(self._buffer)

    def clear_buffer(self) -> None:
        """Clear all buffered measurements."""
        self._buffer.clear()
        self._tare_a = None
        self._tare_b = None
        logger.info("Buffer cleared")

    def _on_data_received(self, line: str) -> None:
        """Parse incoming data line and create MeasurementPoint.

        Args:
            line: Raw data line from SerialManager (CR/LF stripped).
        """
        try:
            packet = parse_line(line)
        except ValueError as exc:
            logger.warning("Parse error: %s", exc)
            return

        point = self._packet_to_point(packet)
        self._buffer.append(point)
        self.new_point.emit(point)

    def _packet_to_point(self, packet: ShortPacket | LongPacket) -> MeasurementPoint:
        """Convert a parsed packet to a MeasurementPoint.

        Args:
            packet: Parsed ShortPacket or LongPacket.

        Returns:
            MeasurementPoint with delta values computed from tare.
        """
        if isinstance(packet, ShortPacket):
            freq_a = packet.channel_a.frequency_precise
            freq_b = packet.channel_b.frequency_precise
            acg_a = packet.channel_a.acg
            acg_b = packet.channel_b.acg
            temp_a = packet.channel_a.temperature
            temp_b = packet.channel_b.temperature
        else:
            freq_a = packet.channel_a_base.frequency_precise
            freq_b = packet.channel_b_base.frequency_precise
            acg_a = packet.channel_a_base.acg
            acg_b = packet.channel_b_base.acg
            temp_a = packet.channel_a_base.temperature
            temp_b = packet.channel_b_base.temperature

        delta_f_a = (freq_a - self._tare_a) if self._tare_a is not None else 0.0
        delta_f_b = (freq_b - self._tare_b) if self._tare_b is not None else 0.0

        return MeasurementPoint(
            timestamp=packet.pc_timestamp,
            device_time=packet.device_time,
            freq_a=freq_a,
            freq_b=freq_b,
            delta_f_a=delta_f_a,
            delta_f_b=delta_f_b,
            delta_m_a=0.0,  # Sauerbrey not yet implemented (Phase 5)
            delta_m_b=0.0,
            acg_a=acg_a,
            acg_b=acg_b,
            temp_a=temp_a,
            temp_b=temp_b,
            voltage_ux=packet.voltage_ux,
        )
