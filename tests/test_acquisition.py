"""Tests for AcquisitionEngine."""
import logging
import time

import pytest
from PySide6.QtCore import QCoreApplication

from src.core.acquisition import AcquisitionEngine
from src.core.data_models import MeasurementPoint
from src.core.serial_manager import SerialManager

logger = logging.getLogger(__name__)


@pytest.fixture
def manager(qapp) -> SerialManager:
    mgr = SerialManager()
    mgr.connect("SIMULATOR")
    yield mgr
    mgr.disconnect()


@pytest.fixture
def engine(manager: SerialManager) -> AcquisitionEngine:
    return AcquisitionEngine(manager)


def _wait_for_points(collector: list, count: int, timeout: float = 5.0) -> None:
    """Wait until collector has at least `count` items or timeout."""
    deadline = time.time() + timeout
    while len(collector) < count and time.time() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.05)


def _collect_points(engine: AcquisitionEngine, trigger, count: int = 1, timeout: float = 5.0) -> list[MeasurementPoint]:
    """Collect emitted MeasurementPoint signals."""
    results: list[MeasurementPoint] = []

    def _handler(point):
        results.append(point)

    engine.new_point.connect(_handler)
    trigger()
    _wait_for_points(results, count, timeout)
    engine.new_point.disconnect(_handler)
    return results


def _collect_status(engine: AcquisitionEngine, trigger) -> list[str]:
    """Collect status_changed signals."""
    results: list[str] = []

    def _handler(status):
        results.append(status)

    engine.status_changed.connect(_handler)
    trigger()
    QCoreApplication.processEvents()
    engine.status_changed.disconnect(_handler)
    return results


class TestAcquisitionBasic:
    """Basic acquisition lifecycle."""

    def test_engine_creates(self, engine: AcquisitionEngine) -> None:
        assert engine is not None

    def test_start_emits_status(self, engine: AcquisitionEngine) -> None:
        results = _collect_status(engine, engine.start)
        assert "running" in results
        engine.stop()

    def test_stop_emits_status(self, engine: AcquisitionEngine) -> None:
        engine.start()
        QCoreApplication.processEvents()
        results = _collect_status(engine, engine.stop)
        assert "stopped" in results

    def test_single_produces_point(self, engine: AcquisitionEngine) -> None:
        points = _collect_points(engine, engine.single)
        assert len(points) >= 1
        assert isinstance(points[0], MeasurementPoint)

    def test_point_has_valid_frequencies(self, engine: AcquisitionEngine) -> None:
        points = _collect_points(engine, engine.single)
        point = points[0]
        assert 9_000_000 < point.freq_a < 11_000_000
        assert 9_000_000 < point.freq_b < 11_000_000


class TestAcquisitionTare:
    """Tare (zeroing) functionality."""

    def test_tare_zeros_delta_f(self, engine: AcquisitionEngine) -> None:
        """After tare, the next measurement should have Δf ≈ 0."""
        # Get a first point
        points = _collect_points(engine, engine.single)
        assert len(points) >= 1

        # Tare both channels
        engine.tare("both")

        # Get another point
        points2 = _collect_points(engine, engine.single)
        assert len(points2) >= 1
        point = points2[0]

        # Δf should be close to zero (within simulator noise)
        assert abs(point.delta_f_a) < 5.0
        assert abs(point.delta_f_b) < 5.0

    def test_tare_channel_a_only(self, engine: AcquisitionEngine) -> None:
        points = _collect_points(engine, engine.single)
        assert len(points) >= 1

        engine.tare("A")

        points2 = _collect_points(engine, engine.single)
        assert len(points2) >= 1
        assert abs(points2[0].delta_f_a) < 5.0

    def test_no_tare_shows_zero_delta(self, engine: AcquisitionEngine) -> None:
        """Without tare, Δf and Δm should be 0.0."""
        points = _collect_points(engine, engine.single)
        assert len(points) >= 1
        point = points[0]
        assert point.delta_f_a == 0.0
        assert point.delta_f_b == 0.0
        assert point.delta_m_a == 0.0
        assert point.delta_m_b == 0.0


class TestAcquisitionBuffer:
    """Ring buffer behavior."""

    def test_buffer_starts_empty(self, engine: AcquisitionEngine) -> None:
        assert len(engine.get_buffer()) == 0

    def test_buffer_grows_with_points(self, engine: AcquisitionEngine) -> None:
        _collect_points(engine, engine.single)
        assert len(engine.get_buffer()) == 1

    def test_clear_buffer(self, engine: AcquisitionEngine) -> None:
        _collect_points(engine, engine.single)
        engine.clear_buffer()
        assert len(engine.get_buffer()) == 0

    def test_buffer_bounded(self, engine: AcquisitionEngine) -> None:
        """Buffer should not exceed maxlen."""
        assert engine._buffer.maxlen == 86400


class TestAcquisitionMode:
    """Mode switching."""

    def test_set_mode_fast(self, engine: AcquisitionEngine) -> None:
        engine.set_mode(fast=True)

    def test_set_mode_slow(self, engine: AcquisitionEngine) -> None:
        engine.set_mode(fast=False)
