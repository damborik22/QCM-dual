"""Statistical analysis for QCM measurement data."""
import logging

import numpy as np

logger = logging.getLogger(__name__)


def calc_stats(data: np.ndarray) -> dict[str, float]:
    """Calculate basic statistics for a data array.

    Args:
        data: 1D array of values.

    Returns:
        Dict with keys: mean, std, min, max, count.
    """
    if len(data) == 0:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    return {
        "mean": float(np.mean(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "count": len(data),
    }


def drift_rate(data: np.ndarray, timestamps: np.ndarray) -> float:
    """Calculate drift rate via linear fit.

    Args:
        data: 1D array of frequency or other values.
        timestamps: 1D array of corresponding time values (seconds).

    Returns:
        Drift rate in units/second. Returns 0.0 if insufficient data.
    """
    if len(data) < 2 or len(timestamps) < 2:
        return 0.0
    coeffs = np.polyfit(timestamps, data, 1)
    return float(coeffs[0])
