"""QCM-Dual protocol parser.

Parses short-format (1×/sec) and long-format (5×/sec) data packets
from the QCM-Dual frequency meter. See docs/PROTOCOL.md for details.
"""
import logging
import time

from src.core.data_models import ChannelData, LongPacket, ShortPacket

logger = logging.getLogger(__name__)

SHORT_FIELD_COUNT = 15  # fields 0-14
LONG_FIELD_COUNT = 31   # fields 0-30


def calculate_checksum(line: str) -> int:
    """Calculate checksum for a QCM data line.

    Sum all ASCII values from start up to and including
    the last tab before the checksum field.

    Args:
        line: Raw data line (may include CR/LF).

    Returns:
        Checksum as integer.
    """
    stripped = line.rstrip("\r\n")
    last_tab_pos = stripped.rfind("\t")
    if last_tab_pos < 0:
        return 0
    payload = stripped[:last_tab_pos + 1]
    return sum(ord(c) for c in payload) % 256


def validate_checksum(line: str) -> bool:
    """Validate the checksum of a QCM data line.

    Args:
        line: Raw data line (may include CR/LF).

    Returns:
        True if the checksum matches.
    """
    stripped = line.rstrip("\r\n")
    fields = stripped.split("\t")
    if len(fields) < 2:
        return False
    try:
        expected = int(fields[-1])
    except ValueError:
        return False
    return calculate_checksum(stripped) == expected


def parse_short(line: str) -> ShortPacket:
    """Parse a short-format (1×/sec) data packet.

    Args:
        line: Tab-separated data line starting with lowercase "qcm".

    Returns:
        Parsed ShortPacket.

    Raises:
        ValueError: If the line has wrong number of fields or cannot be parsed.
    """
    stripped = line.rstrip("\r\n")
    fields = stripped.split("\t")
    if len(fields) != SHORT_FIELD_COUNT:
        raise ValueError(
            f"Short packet expects {SHORT_FIELD_COUNT} fields, got {len(fields)}"
        )

    checksum_valid = validate_checksum(stripped)

    channel_a = ChannelData(
        frequency_int=int(fields[7]),
        frequency_precise=float(fields[9]),
        acg=float(fields[8]),
        temperature=float(fields[6]),
    )
    channel_b = ChannelData(
        frequency_int=int(fields[11]),
        frequency_precise=float(fields[13]),
        acg=float(fields[12]),
        temperature=float(fields[10]),
    )

    return ShortPacket(
        header=fields[0],
        hw_version=fields[1],
        status=int(fields[2]),
        last_command=fields[3],
        device_time=int(fields[4]),
        voltage_ux=float(fields[5]),
        channel_a=channel_a,
        channel_b=channel_b,
        checksum_valid=checksum_valid,
        pc_timestamp=time.time(),
    )


def parse_long(line: str) -> LongPacket:
    """Parse a long-format (5×/sec) data packet.

    Args:
        line: Tab-separated data line starting with uppercase "QCM".

    Returns:
        Parsed LongPacket.

    Raises:
        ValueError: If the line has wrong number of fields or cannot be parsed.
    """
    stripped = line.rstrip("\r\n")
    fields = stripped.split("\t")
    if len(fields) != LONG_FIELD_COUNT:
        raise ValueError(
            f"Long packet expects {LONG_FIELD_COUNT} fields, got {len(fields)}"
        )

    checksum_valid = validate_checksum(stripped)

    # Channel A: base data from fields 6-9, sub-measurements from fields 8-17
    # Field 6=temp_a, 7=freq_a_int, 8=acg_a[0], 9=freq_a[0], ...
    channel_a_base = ChannelData(
        frequency_int=int(fields[7]),
        frequency_precise=float(fields[9]),
        acg=float(fields[8]),
        temperature=float(fields[6]),
    )
    channel_a_subs: list[tuple[float, float]] = []
    for i in range(5):
        acg_idx = 8 + i * 2
        freq_idx = 9 + i * 2
        channel_a_subs.append((float(fields[acg_idx]), float(fields[freq_idx])))

    # Channel B: fields 18-29
    # Field 18=temp_b, 19=freq_b_int, 20=acg_b[0], 21=freq_b[0], ...
    channel_b_base = ChannelData(
        frequency_int=int(fields[19]),
        frequency_precise=float(fields[21]),
        acg=float(fields[20]),
        temperature=float(fields[18]),
    )
    channel_b_subs: list[tuple[float, float]] = []
    for i in range(5):
        acg_idx = 20 + i * 2
        freq_idx = 21 + i * 2
        channel_b_subs.append((float(fields[acg_idx]), float(fields[freq_idx])))

    return LongPacket(
        header=fields[0],
        hw_version=fields[1],
        status=int(fields[2]),
        last_command=fields[3],
        device_time=int(fields[4]),
        voltage_ux=float(fields[5]),
        channel_a_base=channel_a_base,
        channel_a_subs=channel_a_subs,
        channel_b_base=channel_b_base,
        channel_b_subs=channel_b_subs,
        checksum_valid=checksum_valid,
        pc_timestamp=time.time(),
    )


def parse_line(line: str) -> ShortPacket | LongPacket:
    """Auto-detect packet format and parse.

    Args:
        line: Raw data line from the device.

    Returns:
        ShortPacket or LongPacket.

    Raises:
        ValueError: If the format cannot be detected or parsing fails.
    """
    stripped = line.rstrip("\r\n")
    if not stripped:
        raise ValueError("Empty line")

    if stripped.startswith("qcm"):
        return parse_short(stripped)
    elif stripped.startswith("QCM"):
        return parse_long(stripped)
    else:
        raise ValueError(f"Unknown packet format: {stripped[:10]!r}")
