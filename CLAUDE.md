# QCM-Dual Control Software

Dual-channel QCM frequency meter control app.
Python 3.11+ / PySide6 / pyqtgraph / pyserial.

## Read these first
- `docs/SPEC.md` — technical spec (data models, GUI layout, interfaces)
- `docs/PROTOCOL.md` — device protocol (commands, data formats, checksum)
- `docs/PLAN.md` — development phases, acceptance criteria, workflow tips

## Project layout
- `src/core/` — serial I/O, protocol parser, data models, simulator
- `src/processing/` — Sauerbrey, filters, statistics
- `src/gui/` — PySide6 widgets, main window, plots, styles
- `src/export/` — CSV, XLSX, HDF5
- `tests/` — pytest tests + sample data in tests/sample_data/

## Build & run
- Install: `pip install -e ".[dev]"`
- Run: `python -m src.main`
- Test: `pytest tests/ -v`
- Single test: `pytest tests/test_protocol.py::test_parse_short -v`
- Build exe: `pyinstaller qcm_dual.spec`

## Rules
- Type hints on all function signatures
- Dataclasses for structured data — no raw dicts
- Qt Signals/Slots for ALL cross-component communication
- ALL serial I/O in QThread via SerialManager only — never import pyserial elsewhere
- Channel A = blue (#4fc3f7), Channel B = red (#ef5350) everywhere
- Frequency: float Hz. Mass: float ng/cm². Temp 99.9 = disconnected → show "---"
- Google-style docstrings. `logger = logging.getLogger(__name__)` in every module

## When compacting
Preserve: current phase, completed/remaining files, failing test details,
acceptance criteria for current phase.
