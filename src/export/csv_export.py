"""CSV export for QCM-Dual measurement data.

Exports MeasurementPoint buffer as tab-separated CSV with metadata header.
"""
import datetime
import logging
from pathlib import Path

from src.core.data_models import MeasurementPoint

logger = logging.getLogger(__name__)


def _build_header(
    experiment_name: str,
    recording_index: int | None,
    recordings: list[tuple[int, int]] | None,
    tare_a: float | None,
    tare_b: float | None,
    f0: float,
    area: float,
    point_count: int,
) -> list[str]:
    """Build metadata header lines."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# QCM-Dual Export",
        f"# Date: {now}",
    ]
    if experiment_name:
        lines.append(f"# Experiment: {experiment_name}")
    if recording_index is not None:
        lines.append(f"# Recording: {recording_index}")
    if recordings:
        lines.append(f"# Recordings: {len(recordings)}")
    lines.append(f"# Sauerbrey f0: {f0:.0f} Hz, Area: {area} cm\u00b2")
    if tare_a is not None:
        lines.append(f"# Tare A: {tare_a:.3f} Hz")
    if tare_b is not None:
        lines.append(f"# Tare B: {tare_b:.3f} Hz")
    lines.append(f"# Points: {point_count}")
    lines.append("#")
    return lines


def _build_recording_map(
    total_points: int,
    recordings: list[tuple[int, int]] | None,
) -> list[int]:
    """Build a list mapping each point index to its recording number (0=none)."""
    rec_map = [0] * total_points
    if recordings:
        for i, (start, end) in enumerate(recordings):
            for idx in range(start, min(end, total_points)):
                rec_map[idx] = i + 1
    return rec_map


def _write_points(
    f,
    points: list[MeasurementPoint],
    columns: list[str],
    t0: float,
    rec_map: list[int] | None = None,
    point_offset: int = 0,
) -> None:
    """Write column header and data rows."""
    f.write("\t".join(columns) + "\n")

    for i, pt in enumerate(points):
        elapsed = pt.timestamp - t0
        dt = datetime.datetime.fromtimestamp(pt.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]
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
        if rec_map is not None:
            row.append(str(rec_map[point_offset + i]))
        f.write("\t".join(row) + "\n")


def export_csv(
    points: list[MeasurementPoint],
    path: Path,
    experiment_name: str = "",
    recording_index: int | None = None,
    recordings: list[tuple[int, int]] | None = None,
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
        recording_index: Which recording this is (1-based), for individual files.
        recordings: List of (start_idx, end_idx) for marking in full export.
        tare_a: Tare reference frequency for channel A (Hz).
        tare_b: Tare reference frequency for channel B (Hz).
        f0: Sauerbrey fundamental frequency (Hz).
        area: Sauerbrey electrode area (cm²).
        harmonic: Sauerbrey harmonic number.
    """
    path = Path(path)

    header = _build_header(
        experiment_name, recording_index, recordings,
        tare_a, tare_b, f0, area, len(points),
    )

    base_columns = [
        "elapsed_s", "datetime", "device_time", "freq_a", "freq_b",
        "delta_f_a", "delta_f_b", "delta_m_a", "delta_m_b",
        "acg_a", "acg_b", "temp_a", "temp_b", "ux",
    ]

    # Add recording column for full-buffer export
    has_rec_column = recordings is not None and recording_index is None
    columns = base_columns + (["recording"] if has_rec_column else [])

    rec_map = _build_recording_map(len(points), recordings) if has_rec_column else None
    t0 = points[0].timestamp if points else 0.0

    with path.open("w", encoding="utf-8") as f:
        for line in header:
            f.write(line + "\n")
        _write_points(f, points, columns, t0, rec_map)

    logger.info("Exported %d points to %s", len(points), path)
