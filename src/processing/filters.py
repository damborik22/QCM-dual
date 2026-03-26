"""Signal filters for QCM data smoothing."""
import logging

import numpy as np
from scipy.signal import savgol_filter

logger = logging.getLogger(__name__)


def moving_average(data: np.ndarray, window: int) -> np.ndarray:
    """Apply moving average filter.

    Args:
        data: 1D input array.
        window: Window size (must be odd, will be adjusted if even).

    Returns:
        Smoothed array, same length as input (edges padded).
    """
    if window < 2 or len(data) < window:
        return data.copy()
    kernel = np.ones(window) / window
    return np.convolve(data, kernel, mode="same")


def savitzky_golay(data: np.ndarray, window: int, order: int = 3) -> np.ndarray:
    """Apply Savitzky-Golay filter.

    Args:
        data: 1D input array.
        window: Window size (must be odd, >= order + 2).
        order: Polynomial order (default 3).

    Returns:
        Smoothed array, same length as input.
    """
    if window % 2 == 0:
        window += 1
    if window < order + 2:
        window = order + 2
        if window % 2 == 0:
            window += 1
    if len(data) < window:
        return data.copy()
    return savgol_filter(data, window, order)
