"""Tests for QCM-Dual protocol parser."""
import logging
from pathlib import Path

import pytest

from src.core.data_models import ChannelData, LongPacket, ShortPacket
from src.core.protocol import (
    calculate_checksum,
    parse_line,
    parse_long,
    parse_short,
    validate_checksum,
)

logger = logging.getLogger(__name__)

SAMPLE_DIR = Path(__file__).parent / "sample_data"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def short_line() -> str:
    """Raw short-packet line from sample data."""
    return (SAMPLE_DIR / "short_packet.txt").read_text().strip()


@pytest.fixture
def long_line() -> str:
    """Raw long-packet line from sample data."""
    return (SAMPLE_DIR / "long_packet.txt").read_text().strip()


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------

class TestChecksum:
    """Checksum calculation and validation."""

    def test_calculate_checksum_short(self, short_line: str) -> None:
        assert calculate_checksum(short_line) == 99

    def test_calculate_checksum_long(self, long_line: str) -> None:
        assert calculate_checksum(long_line) == 217

    def test_validate_checksum_valid(self, short_line: str) -> None:
        assert validate_checksum(short_line) is True

    def test_validate_checksum_corrupted(self, short_line: str) -> None:
        corrupted = short_line.replace("09979521", "09979522")
        assert validate_checksum(corrupted) is False

    def test_validate_checksum_with_crlf(self, short_line: str) -> None:
        line_with_crlf = short_line + "\r\n"
        assert validate_checksum(line_with_crlf) is True


# ---------------------------------------------------------------------------
# Short packet parsing
# ---------------------------------------------------------------------------

class TestParseShort:
    """Parse short-format (1×/sec) data packets."""

    def test_parse_short_returns_short_packet(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert isinstance(pkt, ShortPacket)

    def test_parse_short_header(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.header == "qcm09"

    def test_parse_short_hw_version(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.hw_version == "5f"

    def test_parse_short_status(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.status == 0

    def test_parse_short_last_command(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.last_command == "A"

    def test_parse_short_device_time(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.device_time == 421

    def test_parse_short_voltage(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.voltage_ux == pytest.approx(0.00015)

    def test_parse_short_channel_a(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        ch = pkt.channel_a
        assert isinstance(ch, ChannelData)
        assert ch.frequency_int == 9979521
        assert ch.frequency_precise == pytest.approx(9979521.207)
        assert ch.acg == pytest.approx(1.44061)
        assert ch.temperature == pytest.approx(99.9)

    def test_parse_short_channel_b(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        ch = pkt.channel_b
        assert isinstance(ch, ChannelData)
        assert ch.frequency_int == 9992541
        assert ch.frequency_precise == pytest.approx(9992540.807)
        assert ch.acg == pytest.approx(1.47993)
        assert ch.temperature == pytest.approx(99.9)

    def test_parse_short_checksum_valid(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.checksum_valid is True

    def test_parse_short_checksum_invalid(self, short_line: str) -> None:
        corrupted = short_line.replace("09979521", "09979522")
        pkt = parse_short(corrupted)
        assert pkt.checksum_valid is False

    def test_parse_short_all_14_fields(self, short_line: str) -> None:
        """Verify all 15 tab-separated fields (0-14) are extracted."""
        pkt = parse_short(short_line)
        assert pkt.header == "qcm09"
        assert pkt.hw_version == "5f"
        assert pkt.status == 0
        assert pkt.last_command == "A"
        assert pkt.device_time == 421
        assert pkt.voltage_ux == pytest.approx(0.00015)
        assert pkt.channel_a.temperature == pytest.approx(99.9)
        assert pkt.channel_a.frequency_int == 9979521
        assert pkt.channel_a.acg == pytest.approx(1.44061)
        assert pkt.channel_a.frequency_precise == pytest.approx(9979521.207)
        assert pkt.channel_b.temperature == pytest.approx(99.9)
        assert pkt.channel_b.frequency_int == 9992541
        assert pkt.channel_b.acg == pytest.approx(1.47993)
        assert pkt.channel_b.frequency_precise == pytest.approx(9992540.807)

    def test_parse_short_pc_timestamp_set(self, short_line: str) -> None:
        pkt = parse_short(short_line)
        assert pkt.pc_timestamp > 0


# ---------------------------------------------------------------------------
# Long packet parsing
# ---------------------------------------------------------------------------

class TestParseLong:
    """Parse long-format (5×/sec) data packets."""

    def test_parse_long_returns_long_packet(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert isinstance(pkt, LongPacket)

    def test_parse_long_header(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.header == "QCM09"

    def test_parse_long_hw_version(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.hw_version == "5d"

    def test_parse_long_status(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.status == 0

    def test_parse_long_last_command(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.last_command == "C"

    def test_parse_long_device_time(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.device_time == 394

    def test_parse_long_voltage(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.voltage_ux == pytest.approx(0.00020)

    def test_parse_long_channel_a_base(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        ch = pkt.channel_a_base
        assert ch.frequency_int == 9979727
        assert ch.frequency_precise == pytest.approx(9979726.947)
        assert ch.acg == pytest.approx(1.48871)
        assert ch.temperature == pytest.approx(99.9)

    def test_parse_long_channel_a_5_subs(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert len(pkt.channel_a_subs) == 5
        # First sub-measurement (T₀)
        assert pkt.channel_a_subs[0] == pytest.approx((1.48871, 9979726.947))
        # Second sub (T₀ + 0.2s)
        assert pkt.channel_a_subs[1] == pytest.approx((1.48868, 9979726.901))
        # Third sub (T₀ + 0.4s)
        assert pkt.channel_a_subs[2] == pytest.approx((1.48873, 9979726.897))
        # Fourth sub (T₀ + 0.6s)
        assert pkt.channel_a_subs[3] == pytest.approx((1.48873, 9979726.927))
        # Fifth sub (T₀ + 0.8s)
        assert pkt.channel_a_subs[4] == pytest.approx((1.48868, 9979726.880))

    def test_parse_long_channel_b_base(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        ch = pkt.channel_b_base
        assert ch.frequency_int == 9992325
        assert ch.frequency_precise == pytest.approx(9992324.788)
        assert ch.acg == pytest.approx(1.41734)
        assert ch.temperature == pytest.approx(99.9)

    def test_parse_long_channel_b_5_subs(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert len(pkt.channel_b_subs) == 5
        # First sub
        assert pkt.channel_b_subs[0] == pytest.approx((1.41734, 9992324.788))
        # Second sub
        assert pkt.channel_b_subs[1] == pytest.approx((1.41732, 9992324.788))
        # Third sub
        assert pkt.channel_b_subs[2] == pytest.approx((1.41733, 9992324.762))
        # Fourth sub
        assert pkt.channel_b_subs[3] == pytest.approx((1.41730, 9992324.749))
        # Fifth sub
        assert pkt.channel_b_subs[4] == pytest.approx((1.41729, 9992324.758))

    def test_parse_long_checksum_valid(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.checksum_valid is True

    def test_parse_long_pc_timestamp_set(self, long_line: str) -> None:
        pkt = parse_long(long_line)
        assert pkt.pc_timestamp > 0


# ---------------------------------------------------------------------------
# Auto-detect via parse_line
# ---------------------------------------------------------------------------

class TestParseLine:
    """parse_line auto-detects short vs long format."""

    def test_parse_line_short(self, short_line: str) -> None:
        pkt = parse_line(short_line)
        assert isinstance(pkt, ShortPacket)

    def test_parse_line_long(self, long_line: str) -> None:
        pkt = parse_line(long_line)
        assert isinstance(pkt, LongPacket)

    def test_parse_line_invalid_header(self) -> None:
        with pytest.raises(ValueError, match="Unknown packet format"):
            parse_line("INVALID\t1\t2\t3")

    def test_parse_line_empty(self) -> None:
        with pytest.raises(ValueError):
            parse_line("")

    @pytest.mark.parametrize("field_count", [5, 10, 13])
    def test_parse_short_wrong_field_count(self, field_count: int) -> None:
        fields = "\t".join(["x"] * field_count)
        line = f"qcm09\t{fields}"
        with pytest.raises(ValueError):
            parse_short(line)
