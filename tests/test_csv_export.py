"""Tests for CSV export."""
import logging
from pathlib import Path

import pytest

from src.core.data_models import MeasurementPoint
from src.export.csv_export import export_csv

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_points() -> list[MeasurementPoint]:
    return [
        MeasurementPoint(
            timestamp=1000000.0 + i,
            device_time=100 + i,
            freq_a=9979521.207 + i * 0.1,
            freq_b=9992540.807 + i * 0.1,
            delta_f_a=-12.35 + i * 0.01,
            delta_f_b=-3.21 + i * 0.01,
            delta_m_a=54.63 - i * 0.05,
            delta_m_b=14.18 - i * 0.05,
            acg_a=1.44061,
            acg_b=1.47993,
            temp_a=23.4,
            temp_b=99.9,
            voltage_ux=0.00015,
        )
        for i in range(5)
    ]


class TestCSVExport:
    """CSV file export."""

    def test_creates_file(self, tmp_path: Path, sample_points: list) -> None:
        path = tmp_path / "test.csv"
        export_csv(sample_points, path)
        assert path.exists()

    def test_header_present(self, tmp_path: Path, sample_points: list) -> None:
        path = tmp_path / "test.csv"
        export_csv(sample_points, path)
        text = path.read_text()
        assert text.startswith("# QCM-Dual Export")

    def test_tare_in_header(self, tmp_path: Path, sample_points: list) -> None:
        path = tmp_path / "test.csv"
        export_csv(sample_points, path, tare_a=9979521.0, tare_b=9992540.0)
        text = path.read_text()
        assert "Tare A: 9979521.000" in text
        assert "Tare B: 9992540.000" in text

    def test_column_header(self, tmp_path: Path, sample_points: list) -> None:
        path = tmp_path / "test.csv"
        export_csv(sample_points, path)
        lines = path.read_text().splitlines()
        data_lines = [l for l in lines if not l.startswith("#")]
        assert data_lines[0].startswith("timestamp\t")
        assert "freq_a" in data_lines[0]

    def test_data_rows(self, tmp_path: Path, sample_points: list) -> None:
        path = tmp_path / "test.csv"
        export_csv(sample_points, path)
        lines = path.read_text().splitlines()
        data_lines = [l for l in lines if not l.startswith("#")]
        # Header + 5 data rows
        assert len(data_lines) == 6

    def test_tab_separated(self, tmp_path: Path, sample_points: list) -> None:
        path = tmp_path / "test.csv"
        export_csv(sample_points, path)
        lines = path.read_text().splitlines()
        data_lines = [l for l in lines if not l.startswith("#")]
        fields = data_lines[1].split("\t")
        assert len(fields) == 13

    def test_decimal_point(self, tmp_path: Path, sample_points: list) -> None:
        """Values should use decimal point, not comma."""
        path = tmp_path / "test.csv"
        export_csv(sample_points, path)
        lines = path.read_text().splitlines()
        data_lines = [l for l in lines if not l.startswith("#")]
        for line in data_lines[1:]:
            # No commas in numeric data
            assert "," not in line

    def test_empty_points(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        export_csv([], path)
        assert path.exists()
        lines = path.read_text().splitlines()
        data_lines = [l for l in lines if not l.startswith("#")]
        assert len(data_lines) == 1  # just column header
