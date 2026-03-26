"""Tests for QCM-Dual simulator."""
import logging

import pytest

from src.core.protocol import parse_line, parse_long, parse_short, validate_checksum
from src.core.simulator import QCMSimulator

logger = logging.getLogger(__name__)


@pytest.fixture
def simulator() -> QCMSimulator:
    return QCMSimulator()


class TestSimulatorShort:
    """Simulator generates valid short packets."""

    def test_short_packet_parses(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        pkt = parse_short(line)
        assert pkt.header.startswith("qcm")

    def test_short_packet_valid_checksum(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        assert validate_checksum(line) is True

    def test_short_packet_frequencies_reasonable(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        pkt = parse_short(line)
        assert 9_000_000 < pkt.channel_a.frequency_precise < 11_000_000
        assert 9_000_000 < pkt.channel_b.frequency_precise < 11_000_000

    def test_short_packet_acg_reasonable(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        pkt = parse_short(line)
        assert 0.5 < pkt.channel_a.acg < 3.0
        assert 0.5 < pkt.channel_b.acg < 3.0

    def test_short_packet_device_time_increments(self, simulator: QCMSimulator) -> None:
        line1 = simulator.generate_short_packet()
        pkt1 = parse_short(line1)
        line2 = simulator.generate_short_packet()
        pkt2 = parse_short(line2)
        assert pkt2.device_time == pkt1.device_time + 1

    def test_short_packet_status_ok(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        pkt = parse_short(line)
        assert pkt.status == 0

    def test_short_packet_voltage_reasonable(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        pkt = parse_short(line)
        assert 0.0 <= pkt.voltage_ux <= 3.2


class TestSimulatorLong:
    """Simulator generates valid long packets."""

    def test_long_packet_parses(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        line = simulator.generate_long_packet()
        pkt = parse_long(line)
        assert pkt.header.startswith("QCM")

    def test_long_packet_valid_checksum(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        line = simulator.generate_long_packet()
        assert validate_checksum(line) is True

    def test_long_packet_5_subs_per_channel(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        line = simulator.generate_long_packet()
        pkt = parse_long(line)
        assert len(pkt.channel_a_subs) == 5
        assert len(pkt.channel_b_subs) == 5

    def test_long_packet_sub_frequencies_close(self, simulator: QCMSimulator) -> None:
        """Sub-measurement frequencies should be close to the base."""
        simulator.set_mode(fast=True)
        line = simulator.generate_long_packet()
        pkt = parse_long(line)
        base_a = pkt.channel_a_base.frequency_precise
        for acg, freq in pkt.channel_a_subs:
            assert abs(freq - base_a) < 50.0

    def test_long_packet_device_time_increments(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        line1 = simulator.generate_long_packet()
        pkt1 = parse_long(line1)
        line2 = simulator.generate_long_packet()
        pkt2 = parse_long(line2)
        assert pkt2.device_time == pkt1.device_time + 1


class TestSimulatorMode:
    """Mode switching behavior."""

    def test_default_mode_is_slow(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        assert line.startswith("qcm")

    def test_set_fast_mode(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        line = simulator.generate_long_packet()
        assert line.startswith("QCM")

    def test_set_slow_mode(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        simulator.set_mode(fast=False)
        line = simulator.generate_short_packet()
        assert line.startswith("qcm")


class TestSimulatorAutoDetect:
    """Simulator output works with parse_line auto-detection."""

    def test_short_via_parse_line(self, simulator: QCMSimulator) -> None:
        line = simulator.generate_short_packet()
        pkt = parse_line(line)
        assert pkt.header.startswith("qcm")

    def test_long_via_parse_line(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        line = simulator.generate_long_packet()
        pkt = parse_line(line)
        assert pkt.header.startswith("QCM")


class TestSimulatorMultiplePackets:
    """Generate many packets without error — stress test for parser."""

    def test_100_short_packets(self, simulator: QCMSimulator) -> None:
        for _ in range(100):
            line = simulator.generate_short_packet()
            pkt = parse_short(line)
            assert pkt.checksum_valid is True

    def test_100_long_packets(self, simulator: QCMSimulator) -> None:
        simulator.set_mode(fast=True)
        for _ in range(100):
            line = simulator.generate_long_packet()
            pkt = parse_long(line)
            assert pkt.checksum_valid is True
