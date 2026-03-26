"""Experiment method (preset) for QCM-Dual.

A Method stores all instrument and processing parameters.
Saved as .qcm files (JSON format).
"""
import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Method:
    """Experiment method / preset."""

    # Metadata
    name: str = "Untitled"
    description: str = ""
    author: str = ""

    # Instrument setup (sent as commands on Start)
    mode_fast: bool = False
    auto_tune_a: bool = True
    auto_tune_b: bool = True
    io_mode_a: str = "NC"
    io_mode_b: str = "NC"

    # Temperature calibration offsets (cumulative D/E/U/V presses)
    temp_cal_offset_a: float = 0.0
    temp_cal_offset_b: float = 0.0

    # Sauerbrey / crystal parameters
    sauerbrey_f0: float = 10_000_000.0
    sauerbrey_area: float = 0.2
    sauerbrey_harmonic: int = 1

    # Display preferences
    plot_y1: str = "delta_f"
    plot_y2: str = "none"
    plot_time_window: int = 600


def save_method(method: Method, path: Path) -> None:
    """Save a method to a .qcm JSON file.

    Args:
        method: The Method to save.
        path: Destination file path.
    """
    path = Path(path)
    data = asdict(method)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Method saved to %s", path)


def load_method(path: Path) -> Method:
    """Load a method from a .qcm JSON file.

    Unknown fields are silently ignored for forward compatibility.
    Missing fields use dataclass defaults.

    Args:
        path: Path to .qcm file.

    Returns:
        Loaded Method.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    known_fields = {f.name for f in fields(Method)}
    filtered = {k: v for k, v in data.items() if k in known_fields}
    logger.info("Method loaded from %s", path)
    return Method(**filtered)
