"""Data models for QCM-Dual measurement data."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChannelData:
    """Single channel measurement data."""
    frequency_int: int          # Integer frequency (Hz)
    frequency_precise: float    # Precise frequency (Hz), e.g. 9979521.207
    acg: float                  # Crystal gain voltage
    temperature: float          # °C, 99.9 means sensor disconnected


@dataclass
class ShortPacket:
    """Parsed short-format data packet (1×/sec)."""
    header: str                 # "qcm09"
    hw_version: str             # "5f"
    status: int                 # 0 = OK
    last_command: str           # e.g. "A"
    device_time: int            # seconds since power-on
    voltage_ux: float           # external voltage (V)
    channel_a: ChannelData
    channel_b: ChannelData
    checksum_valid: bool
    pc_timestamp: float         # time.time() when received


@dataclass
class LongPacket:
    """Parsed long-format data packet (5×/sec)."""
    header: str                 # "QCM09"
    hw_version: str
    status: int
    last_command: str
    device_time: int
    voltage_ux: float
    channel_a_base: ChannelData
    channel_a_subs: list[tuple[float, float]]  # [(acg, precise_freq)] x5
    channel_b_base: ChannelData
    channel_b_subs: list[tuple[float, float]]  # [(acg, precise_freq)] x5
    checksum_valid: bool
    pc_timestamp: float


@dataclass
class MeasurementPoint:
    """Processed point for storage and plotting."""
    timestamp: float            # PC time (time.time())
    device_time: int            # Device uptime (s)
    freq_a: float               # Precise frequency ch A (Hz)
    freq_b: float               # Precise frequency ch B (Hz)
    delta_f_a: float            # freq_a - tare_a
    delta_f_b: float            # freq_b - tare_b
    delta_m_a: float            # Mass change ch A (ng/cm²)
    delta_m_b: float            # Mass change ch B (ng/cm²)
    acg_a: float
    acg_b: float
    temp_a: float               # 99.9 = disconnected
    temp_b: float
    voltage_ux: float
