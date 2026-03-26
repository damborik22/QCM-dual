# QCM-Dual Control Software

Desktop application for the **QCM-Dual frequency meter** — a dual-channel Quartz Crystal Microbalance device manufactured by [KEVA](mailto:p.krasen@gmail.com) (Ing. Pavel Krasensky, Brno, Czech Republic).

The software provides real-time control, data acquisition, visualization, and export for QCM experiments including thin-film deposition, biosensing, and surface chemistry studies.

## Features

- **Dual-channel frequency monitoring** — simultaneous measurement of two QCM sensors at 1×/s or 5×/s
- **Reference channel subtraction** — select one channel as reference to compensate for environmental drift (temperature, pressure)
- **Sauerbrey mass calculation** — real-time conversion of frequency change (Δf) to mass change (Δm) in ng/cm²
- **Dark-themed GUI** — modern PySide6 interface with pyqtgraph real-time plotting
- **Interactive plot** — toggle traces on/off, color-coded Y-axis labels, crosshair with coordinate readout
- **Measurement recording** — mark experiment regions within continuous data, multiple recordings per session shown as highlighted bands on the plot
- **Auto-tare workflow** — tare zeros frequencies, plot auto-switches from raw frequency to Δf view
- **CSV export** — tab-separated data with metadata header, exports recorded measurement window
- **Auto-save safety net** — data auto-saved to `~/.qcm-dual/autosave/` before clearing
- **Method files** — save/load experiment presets (`.qcm` JSON) with instrument and display settings
- **Built-in simulator** — full operation without hardware for testing and demonstration
- **Device settings** — DDS auto-tuning, I/O connector configuration (SMB/BNC), temperature calibration

## Screenshot

*Launch with `.venv/bin/python3 -m src.main` and connect to SIMULATOR to see the interface.*

## Quick Start

```bash
# Clone
git clone git@github.com:damborik22/QCM-dual.git
cd QCM-dual

# Set up environment (requires Python 3.11+)
uv venv .venv
uv pip install -e ".[dev]"

# Run
.venv/bin/python3 -m src.main

# Run tests
.venv/bin/pytest tests/ -v
```

## Typical Workflow

1. **Connect** — select SIMULATOR (or a real COM port) and click Connect
2. **Start receiving** — click ▶ Start, watch frequencies stabilize
3. **Select reference** — choose Ch A or Ch B as reference channel
4. **Tare** — when baseline is stable, press Tare (plot auto-switches to Δf)
5. **Record** — press ⏺ Record to mark experiment start
6. **Run experiment** — inject sample, deposit film, etc.
7. **Stop recording** — press ⏺ again to mark experiment end
8. **Export** — File > Export CSV saves the recorded measurement window

## Project Structure

```
src/
├── main.py                  # Application entry point
├── app_controller.py        # Wires all components together
├── config.py                # QSettings wrapper
├── core/
│   ├── data_models.py       # ChannelData, ShortPacket, LongPacket, MeasurementPoint
│   ├── protocol.py          # Protocol parser (short/long format, checksum)
│   ├── simulator.py         # Built-in QCM device simulator
│   ├── serial_manager.py    # Serial I/O in QThread + SimulatorPort
│   ├── acquisition.py       # Ring buffer, tare, Sauerbrey integration
│   └── method.py            # Method (experiment preset) save/load
├── gui/
│   ├── styles.py            # Dark QSS theme + color constants
│   ├── main_window.py       # QMainWindow with 4 zones + menus
│   ├── connection_panel.py  # Port selection, connect button, status LED
│   ├── control_panel.py     # Start/Stop, Record, Rate, Reference
│   ├── display_panel.py     # Channel cards (A, B, Diff)
│   ├── plot_widget.py       # pyqtgraph with trace toggles + recording bands
│   └── device_settings_dialog.py  # Tune, I/O, temperature calibration
├── processing/
│   ├── sauerbrey.py         # Δf → Δm conversion (Sauerbrey equation)
│   ├── filters.py           # Moving average, Savitzky-Golay
│   └── statistics.py        # Mean, std, drift rate
└── export/
    └── csv_export.py        # Tab-separated CSV with metadata header
```

## Tech Stack

- **Python 3.11+**
- **PySide6** — Qt6 GUI framework
- **pyqtgraph** — real-time plotting
- **pyserial** — serial communication
- **NumPy / SciPy** — signal processing
- **pytest / pytest-qt** — testing (126 tests)

## Hardware

The QCM-Dual device communicates over USB (virtual COM port, MCP2221 bridge, 38400 baud). See [docs/PROTOCOL.md](docs/PROTOCOL.md) for the full command and data format specification.

## Documentation

- [docs/SPEC.md](docs/SPEC.md) — Technical specification (data models, GUI layout, interfaces)
- [docs/PROTOCOL.md](docs/PROTOCOL.md) — Device communication protocol
- [docs/PLAN.md](docs/PLAN.md) — Development plan and phases

## License

Internal use. Contact KEVA for device inquiries.
