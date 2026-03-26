"""Tests for signal filters."""
import logging

import numpy as np
import pytest

from src.processing.filters import moving_average, savitzky_golay

logger = logging.getLogger(__name__)


@pytest.fixture
def noisy_signal() -> np.ndarray:
    """Sine wave with random noise."""
    t = np.linspace(0, 10, 200)
    return np.sin(t) + np.random.normal(0, 0.3, len(t))


class TestMovingAverage:

    def test_same_length(self, noisy_signal: np.ndarray) -> None:
        result = moving_average(noisy_signal, 5)
        assert len(result) == len(noisy_signal)

    def test_reduces_noise(self, noisy_signal: np.ndarray) -> None:
        result = moving_average(noisy_signal, 11)
        assert np.std(result) < np.std(noisy_signal)

    def test_short_data_returns_copy(self) -> None:
        data = np.array([1.0, 2.0])
        result = moving_average(data, 5)
        assert np.array_equal(result, data)

    def test_window_1_is_identity(self) -> None:
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = moving_average(data, 1)
        assert np.array_equal(result, data)


class TestSavitzkyGolay:

    def test_same_length(self, noisy_signal: np.ndarray) -> None:
        result = savitzky_golay(noisy_signal, 11)
        assert len(result) == len(noisy_signal)

    def test_reduces_noise(self, noisy_signal: np.ndarray) -> None:
        result = savitzky_golay(noisy_signal, 11, order=3)
        assert np.std(result) < np.std(noisy_signal)

    def test_even_window_adjusted(self, noisy_signal: np.ndarray) -> None:
        result = savitzky_golay(noisy_signal, 10)
        assert len(result) == len(noisy_signal)

    def test_short_data_returns_copy(self) -> None:
        data = np.array([1.0, 2.0])
        result = savitzky_golay(data, 11)
        assert np.array_equal(result, data)
