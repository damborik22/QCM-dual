"""Tests for statistical analysis."""
import logging

import numpy as np
import pytest

from src.processing.statistics import calc_stats, drift_rate

logger = logging.getLogger(__name__)


class TestCalcStats:

    def test_basic(self) -> None:
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        stats = calc_stats(data)
        assert stats["mean"] == pytest.approx(3.0)
        assert stats["min"] == pytest.approx(1.0)
        assert stats["max"] == pytest.approx(5.0)
        assert stats["count"] == 5

    def test_empty(self) -> None:
        stats = calc_stats(np.array([]))
        assert stats["count"] == 0
        assert stats["mean"] == 0.0

    def test_single_value(self) -> None:
        stats = calc_stats(np.array([42.0]))
        assert stats["mean"] == pytest.approx(42.0)
        assert stats["std"] == pytest.approx(0.0)


class TestDriftRate:

    def test_linear_drift(self) -> None:
        timestamps = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        data = np.array([100.0, 100.5, 101.0, 101.5, 102.0])
        rate = drift_rate(data, timestamps)
        assert rate == pytest.approx(0.5, rel=0.01)

    def test_no_drift(self) -> None:
        timestamps = np.array([0.0, 1.0, 2.0])
        data = np.array([100.0, 100.0, 100.0])
        rate = drift_rate(data, timestamps)
        assert rate == pytest.approx(0.0, abs=0.01)

    def test_insufficient_data(self) -> None:
        assert drift_rate(np.array([1.0]), np.array([0.0])) == 0.0
        assert drift_rate(np.array([]), np.array([])) == 0.0
