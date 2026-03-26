"""Tests for Method dataclass and file I/O."""
import json
import logging
from pathlib import Path

import pytest

from src.core.method import Method, load_method, save_method

logger = logging.getLogger(__name__)


@pytest.fixture
def default_method() -> Method:
    return Method()


@pytest.fixture
def custom_method() -> Method:
    return Method(
        name="Protein adsorption 10MHz",
        description="Standard BSA adsorption protocol",
        author="Lab 3",
        mode_fast=False,
        auto_tune_a=True,
        auto_tune_b=True,
        io_mode_a="NC",
        io_mode_b="NC",
        temp_cal_offset_a=0.3,
        temp_cal_offset_b=0.0,
        sauerbrey_f0=10_000_000.0,
        sauerbrey_area=0.2,
        sauerbrey_harmonic=1,
        plot_y1="delta_f",
        plot_y2="delta_m",
        plot_time_window=1800,
    )


class TestMethodDefaults:
    """Method dataclass has sensible defaults."""

    def test_default_name(self, default_method: Method) -> None:
        assert default_method.name == "Untitled"

    def test_default_mode(self, default_method: Method) -> None:
        assert default_method.mode_fast is False

    def test_default_tune(self, default_method: Method) -> None:
        assert default_method.auto_tune_a is True
        assert default_method.auto_tune_b is True

    def test_default_io(self, default_method: Method) -> None:
        assert default_method.io_mode_a == "NC"
        assert default_method.io_mode_b == "NC"

    def test_default_temp_cal(self, default_method: Method) -> None:
        assert default_method.temp_cal_offset_a == 0.0
        assert default_method.temp_cal_offset_b == 0.0

    def test_default_sauerbrey(self, default_method: Method) -> None:
        assert default_method.sauerbrey_f0 == 10_000_000.0
        assert default_method.sauerbrey_area == 0.2
        assert default_method.sauerbrey_harmonic == 1

    def test_default_plot(self, default_method: Method) -> None:
        assert default_method.plot_y1 == "delta_f"
        assert default_method.plot_y2 == "none"
        assert default_method.plot_time_window == 600


class TestMethodSaveLoad:
    """Save and load .qcm method files."""

    def test_save_creates_file(self, tmp_path: Path, default_method: Method) -> None:
        path = tmp_path / "test.qcm"
        save_method(default_method, path)
        assert path.exists()

    def test_save_is_valid_json(self, tmp_path: Path, default_method: Method) -> None:
        path = tmp_path / "test.qcm"
        save_method(default_method, path)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_round_trip_default(self, tmp_path: Path, default_method: Method) -> None:
        path = tmp_path / "test.qcm"
        save_method(default_method, path)
        loaded = load_method(path)
        assert loaded == default_method

    def test_round_trip_custom(self, tmp_path: Path, custom_method: Method) -> None:
        path = tmp_path / "test.qcm"
        save_method(custom_method, path)
        loaded = load_method(path)
        assert loaded == custom_method

    def test_load_preserves_all_fields(self, tmp_path: Path, custom_method: Method) -> None:
        path = tmp_path / "test.qcm"
        save_method(custom_method, path)
        loaded = load_method(path)
        assert loaded.name == "Protein adsorption 10MHz"
        assert loaded.temp_cal_offset_a == 0.3
        assert loaded.plot_y2 == "delta_m"
        assert loaded.plot_time_window == 1800

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_method(tmp_path / "nonexistent.qcm")

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.qcm"
        path.write_text("not json {{{")
        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_method(path)

    def test_load_ignores_unknown_fields(self, tmp_path: Path) -> None:
        """Forward compatibility: unknown fields are silently ignored."""
        path = tmp_path / "future.qcm"
        data = {"name": "Future", "unknown_field": 42}
        path.write_text(json.dumps(data))
        loaded = load_method(path)
        assert loaded.name == "Future"

    def test_load_missing_fields_use_defaults(self, tmp_path: Path) -> None:
        """Partial files fill missing fields with defaults."""
        path = tmp_path / "partial.qcm"
        path.write_text(json.dumps({"name": "Minimal"}))
        loaded = load_method(path)
        assert loaded.name == "Minimal"
        assert loaded.mode_fast is False
        assert loaded.sauerbrey_f0 == 10_000_000.0
