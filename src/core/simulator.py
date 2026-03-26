"""QCM-Dual device simulator.

Generates realistic QCM data packets for testing without hardware.
See docs/PROTOCOL.md for packet format details.
"""
import logging
import math
import random

logger = logging.getLogger(__name__)


class QCMSimulator:
    """Generates realistic QCM data packets."""

    def __init__(
        self,
        base_freq_a: float = 9_979_500.0,
        base_freq_b: float = 9_992_500.0,
    ) -> None:
        """Initialize with base frequencies for both channels.

        Args:
            base_freq_a: Base frequency for channel A (Hz).
            base_freq_b: Base frequency for channel B (Hz).
        """
        self._base_freq_a = base_freq_a
        self._base_freq_b = base_freq_b
        self._device_time = 0
        self._fast_mode = False
        self._last_command = "A"

        # Random walk state
        self._freq_a = base_freq_a
        self._freq_b = base_freq_b
        self._acg_a = 1.45
        self._acg_b = 1.45
        self._temp_a = 23.0
        self._temp_b = 23.0

    def set_mode(self, fast: bool) -> None:
        """Switch between 1x/s and 5x/s mode.

        Args:
            fast: True for 5x/s (long packets), False for 1x/s (short).
        """
        self._fast_mode = fast
        self._last_command = "G" if fast else "F"

    def process_command(self, cmd: str) -> None:
        """Process a received command, updating internal state.

        Args:
            cmd: Single character command (A-V).
        """
        self._last_command = cmd
        if cmd == "F":
            self._fast_mode = False
        elif cmd == "G":
            self._fast_mode = True

    def generate_short_packet(self) -> str:
        """Return a complete short-format data line with valid checksum.

        Returns:
            Tab-separated ASCII line (no CR/LF terminator).
        """
        self._step()

        freq_a_int = int(round(self._freq_a))
        freq_b_int = int(round(self._freq_b))
        voltage = self._gen_voltage()
        temp_a = self._gen_temperature("a")
        temp_b = self._gen_temperature("b")

        fields = [
            "qcm09",
            "5f",
            "0",
            self._last_command,
            f"{self._device_time:06d}",
            f"{voltage:.5f}",
            f"{temp_a:.1f}",
            f"{freq_a_int:08d}",
            f"{self._acg_a:.5f}",
            f"{self._freq_a:.3f}",
            f"{temp_b:.1f}",
            f"{freq_b_int:08d}",
            f"{self._acg_b:.5f}",
            f"{self._freq_b:.3f}",
        ]

        payload = "\t".join(fields) + "\t"
        checksum = sum(ord(c) for c in payload) % 256
        return payload + str(checksum)

    def generate_long_packet(self) -> str:
        """Return a complete long-format data line with valid checksum.

        Returns:
            Tab-separated ASCII line (no CR/LF terminator).
        """
        self._step()

        freq_a_int = int(round(self._freq_a))
        freq_b_int = int(round(self._freq_b))
        voltage = self._gen_voltage()
        temp_a = self._gen_temperature("a")
        temp_b = self._gen_temperature("b")

        fields: list[str] = [
            "QCM09",
            "5f",
            "0",
            self._last_command,
            f"{self._device_time:06d}",
            f"{voltage:.5f}",
            # Channel A
            f"{temp_a:.1f}",
            f"{freq_a_int:08d}",
        ]

        # 5 sub-measurements for channel A
        for i in range(5):
            sub_acg = self._acg_a + random.gauss(0, 0.00005)
            sub_freq = self._freq_a + random.gauss(0, 0.05)
            fields.append(f"{sub_acg:.5f}")
            fields.append(f"{sub_freq:.3f}")

        # Channel B
        fields.append(f"{temp_b:.1f}")
        fields.append(f"{freq_b_int:08d}")

        # 5 sub-measurements for channel B
        for i in range(5):
            sub_acg = self._acg_b + random.gauss(0, 0.00005)
            sub_freq = self._freq_b + random.gauss(0, 0.05)
            fields.append(f"{sub_acg:.5f}")
            fields.append(f"{sub_freq:.3f}")

        payload = "\t".join(fields) + "\t"
        checksum = sum(ord(c) for c in payload) % 256
        return payload + str(checksum)

    def _step(self) -> None:
        """Advance simulation by one time step."""
        self._device_time += 1
        t = self._device_time

        # Frequency: random walk + slow drift
        self._freq_a += random.gauss(0, 0.5) + 0.01
        self._freq_b += random.gauss(0, 0.5) + 0.01

        # ACG: small random fluctuation around 1.45
        self._acg_a = 1.45 + random.gauss(0, 0.02)
        self._acg_b = 1.45 + random.gauss(0, 0.02)

        # Temperature: slow sinusoidal drift
        self._temp_a = 23.0 + 0.5 * math.sin(2 * math.pi * t / 300)
        self._temp_b = 23.0 + 0.5 * math.sin(2 * math.pi * t / 300 + 0.5)

    def _gen_voltage(self) -> float:
        """Generate realistic external voltage reading."""
        return 0.0002 + random.gauss(0, 0.00005)

    def _gen_temperature(self, channel: str) -> float:
        """Return current temperature for channel.

        Args:
            channel: "a" or "b".

        Returns:
            Temperature in °C. Returns 99.9 if sensor disconnected.
        """
        if channel == "a":
            return self._temp_a
        return self._temp_b
