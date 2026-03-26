# QCM-Dual Software — Technical Specification

## 1. Overview

Desktop application for the QCM-Dual frequency meter: control, data collection,
real-time visualization, processing (Sauerbrey), and export.
Must work fully in **simulator mode** without hardware.

**Target:** Windows 10/11 (primary), Linux (secondary). Single .exe via PyInstaller.

---

## 2. Method Files (src/core/method.py)

A **Method** is a reusable experiment profile that stores all instrument and
processing parameters. Saved as `.qcm` files (JSON). The method defines
**how** to measure; data export (CSV/XLSX/HDF5) stores **what** was measured.

```python
@dataclass
class Method:
    """Experiment method / preset."""
    # Metadata
    name: str = "Untitled"
    description: str = ""
    author: str = ""

    # Instrument setup (sent as commands on Start)
    mode_fast: bool = False           # False=1×/s (F), True=5×/s (G)
    auto_tune_a: bool = True          # True=H, False=I
    auto_tune_b: bool = True          # True=S, False=T
    io_mode_a: str = "NC"             # "NC"=K, "EXT"=J, "LEVER"=L, "10MHZ"=M
    io_mode_b: str = "NC"             # "NC"=P, "EXT"=O, "LEVER"=Q, "10MHZ"=R

    # Temperature calibration offsets (cumulative D/E/U/V presses)
    temp_cal_offset_a: float = 0.0    # °C offset, applied via D/E commands
    temp_cal_offset_b: float = 0.0    # °C offset, applied via U/V commands

    # Sauerbrey / crystal parameters
    sauerbrey_f0: float = 10_000_000.0   # Fundamental frequency (Hz)
    sauerbrey_area: float = 0.2          # Electrode area (cm²)
    sauerbrey_harmonic: int = 1          # Harmonic number (1, 3, 5...)

    # Display preferences
    plot_y1: str = "delta_f"
    plot_y2: str = "none"
    plot_time_window: int = 600       # seconds
    display_mode: str = "all"         # "all" = A+B+Diff, "diff" = Diff only
```

**File format:** JSON with `.qcm` extension.

```json
{
  "name": "Protein adsorption 10MHz",
  "description": "Standard BSA adsorption protocol",
  "author": "Lab 3",
  "mode_fast": false,
  "auto_tune_a": true,
  "auto_tune_b": true,
  "io_mode_a": "NC",
  "io_mode_b": "NC",
  "temp_cal_offset_a": 0.3,
  "temp_cal_offset_b": 0.0,
  "sauerbrey_f0": 10000000.0,
  "sauerbrey_area": 0.2,
  "sauerbrey_harmonic": 1,
  "plot_y1": "delta_f",
  "plot_y2": "delta_m",
  "plot_time_window": 1800
}
```

**File menu behavior:**
- **New**: Reset to default method, clear data buffer
- **Open...**: Load `.qcm` file, apply all settings (instrument + display + Sauerbrey)
- **Save / Save As...**: Save current method as `.qcm`
- **Recent Methods**: Last 5 opened methods for quick access

When the user presses **Start**, the application sends the method's instrument
commands to the device (mode, tune, I/O, temp calibration) before sending 'A'.

---

## 3. Data Models (src/core/data_models.py)

```python
from dataclasses import dataclass, field

@dataclass
class ChannelData:
    frequency_int: int          # Integer frequency (Hz)
    frequency_precise: float    # Precise frequency (Hz), e.g. 9979521.207
    acg: float                  # Crystal gain voltage
    temperature: float          # °C, 99.9 means sensor disconnected

@dataclass
class ShortPacket:
    header: str                 # "qcm09"
    hw_version: str             # "5f"
    status: int                 # 0 = OK
    last_command: str           # e.g. "A"
    device_time: int            # seconds since power-on
    voltage_ux: float           # external voltage (V)
    channel_a: ChannelData
    channel_b: ChannelData
    checksum_valid: bool
    pc_timestamp: float         # time.time() when received

@dataclass
class LongPacket:
    header: str                 # "QCM09"
    hw_version: str
    status: int
    last_command: str
    device_time: int
    voltage_ux: float
    channel_a_base: ChannelData
    channel_a_subs: list[tuple[float, float]]  # [(acg, precise_freq)] x5
    channel_b_base: ChannelData
    channel_b_subs: list[tuple[float, float]]  # [(acg, precise_freq)] x5
    checksum_valid: bool
    pc_timestamp: float

@dataclass
class MeasurementPoint:
    """Processed point for storage and plotting."""
    timestamp: float            # PC time (time.time())
    device_time: int            # Device uptime (s)
    freq_a: float               # Precise frequency ch A (Hz)
    freq_b: float               # Precise frequency ch B (Hz)
    delta_f_a: float            # freq_a - tare_a
    delta_f_b: float            # freq_b - tare_b
    delta_m_a: float            # Mass change ch A (ng/cm²)
    delta_m_b: float            # Mass change ch B (ng/cm²)
    acg_a: float
    acg_b: float
    temp_a: float               # 99.9 = disconnected
    temp_b: float
    voltage_ux: float
```

---

## 4. Core Interfaces

### SerialManager (src/core/serial_manager.py)

```python
class SerialManager(QObject):
    data_received = Signal(str)       # Emits raw line (stripped of CR LF)
    connection_changed = Signal(bool) # True=connected, False=disconnected
    error_occurred = Signal(str)      # Error message

    def get_available_ports(self) -> list[str]:
        """Return list of COM ports + 'SIMULATOR'."""

    def connect(self, port: str) -> bool:
        """Connect to port. If port=='SIMULATOR', use built-in simulator.
        Starts a read thread. Returns True on success."""

    def disconnect(self) -> None:
        """Stop read thread, close port."""

    def send_command(self, cmd: str) -> None:
        """Send single character command (A-V). Thread-safe."""

    def is_connected(self) -> bool:
        """Return current connection state."""
```

**Implementation notes:**
- Read thread: QThread that calls readline() in a loop
- For simulator: create a SimulatorPort object that mimics serial.Serial interface
- Reconnect logic: if USB disconnects, emit connection_changed(False) and attempt
  reconnect every 2 seconds

### AcquisitionEngine (src/core/acquisition.py)

```python
class AcquisitionEngine(QObject):
    new_point = Signal(object)        # Emits MeasurementPoint
    status_changed = Signal(str)      # "running", "stopped", "error"

    def __init__(self, serial_manager: SerialManager):
        """Takes a SerialManager instance. Connects to its data_received signal."""

    def start(self) -> None:          # Sends 'A' command
    def stop(self) -> None:           # Sends 'B' command
    def single(self) -> None:         # Sends 'C' command
    def set_mode(self, fast: bool):   # Sends 'F' (fast=False) or 'G' (fast=True)
    def tare(self, channel: str):     # 'A', 'B', or 'both' — set reference freq
    def get_buffer(self) -> list[MeasurementPoint]:
    def clear_buffer(self) -> None
```

**Implementation notes:**
- Ring buffer: collections.deque(maxlen=86400) — 24h at 1/sec
- On data_received: parse with protocol.py → create MeasurementPoint → emit new_point
- Tare stores current frequency as reference; Δf = current - reference
- Δm computed via Sauerbrey (if processing module available, else 0.0)

### Simulator (src/core/simulator.py)

```python
class QCMSimulator:
    """Generates realistic QCM data packets."""

    def __init__(self, base_freq_a: float = 9_979_500.0,
                 base_freq_b: float = 9_992_500.0):
        """Initialize with base frequencies for both channels."""

    def generate_short_packet(self) -> str:
        """Return a complete short-format data line with valid checksum."""

    def generate_long_packet(self) -> str:
        """Return a complete long-format data line with valid checksum."""

    def set_mode(self, fast: bool) -> None:
        """Switch between 1×/s and 5×/s mode."""
```

**Simulation behavior:**
- Frequency: base ± random walk (σ=0.5 Hz/step) + slow drift (0.01 Hz/s)
- ACG: ~1.45 ± 0.02 random
- Temperature: 23.0 + slow sinusoidal drift (±0.5°C, period 300s), or 99.9
- Voltage: ~0.0002 ± 0.00005
- Device time: increments by 1 each call
- Checksum: calculated correctly per PROTOCOL.md

---

## 5. GUI Layout

Window divided into 4 horizontal zones, top to bottom:

### Zone 1: Top bar — Connection + Control (fixed height ~80px)

Left side: **Connection Panel**
- QComboBox: available ports + "SIMULATOR" (always present)
- QPushButton: "Connect" / "Disconnect" (text toggles)
- QLabel with colored dot: green=connected, red=disconnected, yellow=connecting

Right side: **Control Panel**
- QPushButtons: Start (▶), Stop (⏹), Single (①)
- QButtonGroup with QRadioButtons: "1×/s" and "5×/s"
- QCheckBox × 2: "Tune A", "Tune B" (auto-tuning)
- QComboBox × 2: I/O mode for ch A and ch B
  Options: "NC (off)", "Ext. input", "Lever out", "10 MHz out"
- QPushButtons × 4: "T+A", "T−A", "T+B", "T−B" (temperature calibration ±0.1°C)
  Sends commands D/E (ch A) and U/V (ch B). Current offset shown in tooltip.

### Zone 2: Numeric displays (fixed height ~140px)

Three side-by-side **DisplayPanel** cards (QFrame with styled border):

**Card A** and **Card B** each show:
| Label        | Value format          | Font     |
|--------------|-----------------------|----------|
| Frequency    | 9 979 521.207 Hz     | 18pt mono|
| Δf           | −12.35 Hz            | 14pt mono|
| Δm           | 54.63 ng/cm²         | 14pt mono|
| ACG          | 1.4406 V             | 12pt mono|
| Temperature  | 23.4 °C (or "---")   | 12pt mono|

**Card Diff (A−B)** shows the differential signal:
| Label        | Value format          | Font     |
|--------------|-----------------------|----------|
| Δf (A−B)     | −3.21 Hz             | 18pt mono|
| Δm (A−B)     | 14.18 ng/cm²         | 14pt mono|

- Card A has blue left border accent (#4fc3f7)
- Card B has red left border accent (#ef5350)
- Card Diff has green left border accent (#66bb6a)
- Δf and Δm show "—" until tare is set
- Differential values: Δf_diff = Δf_A − Δf_B, Δm_diff via Sauerbrey on Δf_diff

**Display modes** (View menu or toolbar toggle):
- **All channels**: show Card A + Card B + Card Diff (default)
- **Differential only**: show only Card Diff (expanded width)

### Zone 3: Plot (stretches to fill, minimum 300px)

**PlotWidget** toolbar (above plot):
- QComboBox "Y1": Δf, Frequency, Δm, ACG, Temperature, Δf (A−B), Δm (A−B)
- QComboBox "Y2": None, Δf, Frequency, Δm, ACG, Temperature, Δf (A−B), Δm (A−B)
- QPushButtons: Tare, Autoscale, Clear

Plot features:
- pyqtgraph PlotWidget
- X axis: elapsed time in seconds (auto-ranging)
- Left Y axis: selected parameter, labeled with units
- Right Y axis (optional): second parameter
- Two lines: Ch A (blue #4fc3f7), Ch B (red #ef5350)
- Differential shown as single green line (#66bb6a) when Δf(A−B) or Δm(A−B) selected
- Legend in top-right corner
- Crosshair cursor with coordinate readout at bottom
- Mouse: scroll=zoom, drag=pan
- Background: #1a1a2e, grid: #2a2a4a

### Zone 4: Status bar (standard QStatusBar)

Permanent widgets (left to right):
- Elapsed time: "⏱ 00:07:01"
- Point count: "Points: 421"
- Error count: "Errors: 0"
- Voltage: "Ux: 0.00015 V"
- Mode indicator: "1×/s" or "5×/s"
- Connection: "Simulator" or "COM3" or "Disconnected"

### Menu bar

- **File**: New Method, Open Method..., Save Method, Save Method As...,
  separator, Recent Methods >,
  separator, Export CSV, Export XLSX, Export HDF5, separator, Exit
- **Device**: Connect, Disconnect, separator, Simulator mode, separator, Send command...
- **View**: Show/hide Connection panel, Show/hide Control panel,
  separator, Display: All channels, Display: Differential only,
  separator, Reset layout
- **Tools**: Sauerbrey settings, Temperature calibration, Statistics
- **Help**: About

---

## 6. Theme / Styling (src/gui/styles.py)

Single QSS string applied via `app.setStyleSheet(DARK_THEME)`.

```
Background:       #1e1e2e
Surface/cards:    #2a2a3d, border: 1px solid #3a3a5c, border-radius: 8px
Input fields:     #353550 background, #e0e0e0 text
Text primary:     #e0e0e0
Text secondary:   #8888aa
Accent blue:      #4fc3f7  (channel A, primary buttons, links)
Accent red:       #ef5350  (channel B)
Green:            #66bb6a  (connected, OK status)
Amber:            #ffa726  (warnings)
Buttons:          #353550 background, #e0e0e0 text, flat, hover: #454570
Disabled:         #555555 text, #2a2a3d background
Plot background:  #1a1a2e
Plot grid:        #2a2a4a
Scrollbar:        thin, #3a3a5c handle
```

Font strategy:
- Numeric values: platform monospace (Consolas on Windows, monospace on Linux)
- Labels/UI text: system default
- Large frequency display: 18pt
- Δf/Δm: 14pt
- Other values: 12pt
- Labels: 11pt

---

## 7. Processing

### Sauerbrey (src/processing/sauerbrey.py)

```python
import math

# Quartz constants
MU_Q = 2.947e11   # Shear modulus (g·cm⁻¹·s⁻²)
RHO_Q = 2.648      # Density (g/cm³)

def delta_f_to_delta_m(
    delta_f: float,
    f0: float = 10e6,
    A: float = 0.2,
    n: int = 1
) -> float:
    """Convert frequency change to mass change using Sauerbrey equation.

    Δm = -(Δf × A × √(μq × ρq)) / (2 × n × f0²)

    Args:
        delta_f: Frequency change in Hz (negative = mass added)
        f0: Fundamental resonant frequency in Hz
        A: Active electrode area in cm²
        n: Harmonic number (1, 3, 5...)

    Returns:
        Mass change in ng/cm²
    """
    C = 2 * n * f0**2 / (A * math.sqrt(MU_Q * RHO_Q))
    delta_m_g_per_cm2 = -delta_f / C
    return delta_m_g_per_cm2 * 1e9  # convert g/cm² to ng/cm²
```

### Filters (src/processing/filters.py)

- `moving_average(data: np.ndarray, window: int) -> np.ndarray`
- `savitzky_golay(data: np.ndarray, window: int, order: int) -> np.ndarray`

### Statistics (src/processing/statistics.py)

- `calc_stats(data: np.ndarray) -> dict` — mean, std, min, max
- `drift_rate(data: np.ndarray, timestamps: np.ndarray) -> float` — Hz/s via linear fit

---

## 8. Export Formats

### CSV (src/export/csv_export.py)

```
# QCM-Dual Export
# Date: 2025-01-15 14:30:00
# Device: qcm09, HW: 5f
# Sauerbrey f0: 10000000 Hz, Area: 0.2 cm²
# Tare A: 9979521.207 Hz
# Tare B: 9992540.807 Hz
#
timestamp	device_time	freq_a	freq_b	delta_f_a	delta_f_b	delta_m_a	delta_m_b	acg_a	acg_b	temp_a	temp_b	ux
```

Tab-separated, decimal point (not comma). One row per MeasurementPoint.

### XLSX (src/export/excel_export.py)

- Sheet "Data": same columns as CSV
- Sheet "Metadata": experiment parameters
- Sheet "Statistics": summary stats per channel

### HDF5 (src/export/hdf5_export.py)

- Group "/data" with datasets: timestamp, freq_a, freq_b, delta_f_a, etc.
- Attributes on root group: f0, area, tare_a, tare_b, export_date

---

## 9. Configuration (src/config.py)

Use QSettings("KEVA", "QCM-Dual"):

```python
DEFAULTS = {
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
```
