"""Application configuration using QSettings."""
import logging

from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)

DEFAULTS: dict = {
    "serial/last_port": "SIMULATOR",
    "serial/baud_rate": 38400,
    "measurement/mode_fast": False,
    "measurement/auto_tune_a": True,
    "measurement/auto_tune_b": True,
    "measurement/io_mode_a": "NC",
    "measurement/io_mode_b": "NC",
    "sauerbrey/f0": 10_000_000.0,
    "sauerbrey/area": 0.2,
    "sauerbrey/harmonic": 1,
    "plot/y1_parameter": "delta_f",
    "plot/y2_parameter": "none",
    "plot/time_window": 600,
    "export/delimiter": "tab",
    "export/last_directory": "",
    "method/last_file": "",
    "method/recent_files": [],
    "temp_cal/offset_a": 0.0,
    "temp_cal/offset_b": 0.0,
    "window/geometry": None,
    "window/state": None,
}


def get_settings() -> QSettings:
    """Return the application QSettings instance."""
    return QSettings("KEVA", "QCM-Dual")


def get_value(key: str) -> object:
    """Get a config value, falling back to DEFAULTS.

    Args:
        key: Settings key, e.g. "serial/baud_rate".

    Returns:
        The stored value, or the default.
    """
    settings = get_settings()
    default = DEFAULTS.get(key)
    return settings.value(key, default)


def set_value(key: str, value: object) -> None:
    """Store a config value.

    Args:
        key: Settings key.
        value: Value to store.
    """
    settings = get_settings()
    settings.setValue(key, value)
