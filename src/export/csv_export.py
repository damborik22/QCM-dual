"""CSV export for QCM-Dual measurement data.

Exports MeasurementPoint buffer as tab-separated CSV with metadata header.
"""
import datetime
import logging
from pathlib import Path

from src.core.data_models import MeasurementPoint

logger = logging.getLogger(__name__)


def export_csv(
    points: list[MeasurementPoint],
    path: Path,
    experiment_name: str = "",
    recording_index: int | None = None,
    tare_a: float | None = None,
    tare_b: float | None = None,
    f0: float = 10e6,
    area: float = 0.2,
    harmonic: int = 1,
) -> None:
    """Export measurement data to a tab-separated CSV file.

    Args:
        points: List of MeasurementPoint objects.
        path: Destination file path.
        experiment_name: Name of the experiment.
        recording_index: Which recording this is (1-based), or None.
        tare_a: Tare reference frequency for channel A (Hz).
        tare_b: Tare reference frequency for channel B (Hz).
        f0: Sauerbrey fundamental frequency (Hz).
        area: Sauerbrey electrode area (cm²).
        harmonic: Sauerbrey harmonic number.
    """
    path = Path(path)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header_lines = [
        "# QCM-Dual Export",
        f"# Date: {now}",
    ]
    if experiment_name:
        header_lines.append(f"# Experiment: {experiment_name}")
    if recording_index is not None:
        header_lines.append(f"# Recording: {recording_index}")
    header_lines.append(f"# Sauerbrey f0: {f0:.0f} Hz, Area: {area} cm\u00b2")
    if tare_a is not None:
        header_lines.append(f"# Tare A: {tare_a:.3f} Hz")
    if tare_b is not None:
        header_lines.append(f"# Tare B: {tare_b:.3f} Hz")
    header_lines.append(f"# Points: {len(points)}")
    header_lines.append("#")

    columns = [
        "elapsed_s", "datetime", "device_time", "freq_a", "freq_b",
        "delta_f_a", "delta_f_b", "delta_m_a", "delta_m_b",
        "acg_a", "acg_b", "temp_a", "temp_b", "ux",
    ]

    t0 = points[0].timestamp if points else 0.0

    with path.open("w", encoding="utf-8") as f:
        for line in header_lines:
            f.write(line + "\n")
        f.write("\t".join(columns) + "\n")

        for pt in points:
            elapsed = pt.timestamp - t0
            dt = datetime.datetime.fromtimestamp(pt.timestamp).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )[:-3]  # trim to milliseconds
            row = [
                f"{elapsed:.3f}",
                dt,
                str(pt.device_time),
                f"{pt.freq_a:.3f}",
                f"{pt.freq_b:.3f}",
                f"{pt.delta_f_a:.3f}",
                f"{pt.delta_f_b:.3f}",
                f"{pt.delta_m_a:.3f}",
                f"{pt.delta_m_b:.3f}",
                f"{pt.acg_a:.5f}",
                f"{pt.acg_b:.5f}",
                f"{pt.temp_a:.1f}",
                f"{pt.temp_b:.1f}",
                f"{pt.voltage_ux:.5f}",
            ]
            f.write("\t".join(row) + "\n")

    logger.info("Exported %d points to %s", len(points), path)
