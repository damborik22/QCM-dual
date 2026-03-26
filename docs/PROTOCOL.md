# QCM-Dual Communication Protocol Reference

## Physical Layer

| Parameter    | Value                              |
|--------------|------------------------------------|
| Interface    | USB → Virtual COM port             |
| Bridge IC    | MCP2221 (Microchip)               |
| Baud rate    | 38 400 Bd                         |
| Data bits    | 8                                  |
| Parity       | None                               |
| Stop bits    | 1                                  |
| Flow control | None                               |
| Encoding     | ASCII text                         |
| USB VID:PID  | 04D8:00DD (Microchip MCP2221)     |

Driver: Windows 10/11 usually auto-detects CDC class. If not, install
Microchip MCP2221 driver. On Linux: appears as `/dev/ttyACMx`.

---

## Commands (PC → Device)

Single ASCII character, no terminator needed.

### Measurement Control
| Cmd | Name    | Description                                       |
|-----|---------|---------------------------------------------------|
| A   | START   | Begin continuous data (1 packet/sec)               |
| B   | STOP    | Stop continuous data (after ~1 sec)                |
| C   | SINGLE  | Send one packet, cancels START mode                |
| F   | 1× mode | Set 1 measurement/sec → short data format          |
| G   | 5× mode | Set 5 measurements/sec → long data format          |

### Channel A — DDS Tuning
| Cmd | Name      | Description                                     |
|-----|-----------|-------------------------------------------------|
| H   | LADI_1    | Enable auto-tuning via DDS every second          |
| I   | NELADI_1  | Disable auto-tuning, freeze DDS                  |

### Channel A — I/O Connector (SMB)
| Cmd | Name         | Description                                  |
|-----|--------------|----------------------------------------------|
| J   | EXT_in_1     | SMB = TTL signal input                       |
| K   | NC_1         | SMB = disconnected (recommended default)     |
| L   | LEVER_out_1  | SMB = lever oscillator output                |
| M   | 10MHz_out_1  | SMB = 10 MHz reference clock output          |

### Channel A — Temperature Calibration
| Cmd | Name  | Description                                        |
|-----|-------|----------------------------------------------------|
| D   | INCK3 | Increase temp calibration +0.1°C                   |
| E   | DECK3 | Decrease temp calibration −0.1°C                   |

### Channel B — I/O Connector (BNC)
| Cmd | Name        | Description                                   |
|-----|-------------|-----------------------------------------------|
| O   | EXT_in2     | BNC = external signal input                   |
| P   | NC2         | BNC = disconnected (recommended default)      |
| Q   | LEVER_out2  | BNC = lever oscillator output                 |
| R   | 10MHz_out2  | BNC = 10 MHz reference clock output           |

### Channel B — DDS Tuning
| Cmd | Name    | Description                                       |
|-----|---------|---------------------------------------------------|
| S   | LADI2   | Enable auto-tuning channel B                       |
| T   | NELADI2 | Disable auto-tuning channel B                      |

### Channel B — Temperature Calibration
| Cmd | Name  | Description                                        |
|-----|-------|----------------------------------------------------|
| U   | INCK4 | Increase temp calibration +0.1°C (ch B)            |
| V   | DECK4 | Decrease temp calibration −0.1°C (ch B)            |

### Recommended Defaults
1. Enable auto-tuning: commands H and S
2. Disconnect unused I/O: commands K and P
3. Beat frequency at maximum: 400 Hz (ch A) / 480 Hz (ch B)

---

## Data Formats

All data: tab-separated ASCII, terminated by CR LF (`\r\n`).

### Short Data (1×/sec, set by command F)

Header starts with lowercase `qcm`. Transmission ~20 ms.

**Example:**
```
qcm09\t5f\t0\tA\t000421\t0.00015\t99.9\t09979521\t1.44061\t09979521.207\t99.9\t09992541\t1.47993\t09992540.807\t134\r\n
```

**Field map (tab-separated, 0-indexed):**

| #  | Name             | Type   | Example          | Description                                    |
|----|------------------|--------|------------------|------------------------------------------------|
| 0  | header           | str    | qcm09            | "qcm"=short data, "09"=device version          |
| 1  | hw_version       | str    | 5f               | Hardware/software version                       |
| 2  | status           | int    | 0                | Error code (0=OK)                               |
| 3  | last_command     | str    | A                | Echo of last received command                   |
| 4  | device_time      | int    | 000421           | Seconds since power-on                          |
| 5  | voltage_ux       | float  | 0.00015          | External voltage input (V)                      |
| 6  | temp_a           | float  | 99.9             | Temperature ch A (99.9=disconnected)            |
| 7  | freq_a_int       | int    | 09979521         | Integer frequency ch A (Hz)                     |
| 8  | acg_a            | float  | 1.44061          | Crystal gain ch A                               |
| 9  | freq_a_precise   | float  | 09979521.207     | Precise frequency ch A (Hz)                     |
| 10 | temp_b           | float  | 99.9             | Temperature ch B (99.9=disconnected)            |
| 11 | freq_b_int       | int    | 09992541         | Integer frequency ch B (Hz)                     |
| 12 | acg_b            | float  | 1.47993          | Crystal gain ch B                               |
| 13 | freq_b_precise   | float  | 09992540.807     | Precise frequency ch B (Hz)                     |
| 14 | checksum         | int    | 134              | ASCII sum of all chars up to last tab           |

### Long Data (5×/sec, set by command G)

Header starts with uppercase `QCM`. Transmission ~80 ms.
Contains 5 sub-measurements per channel at 200 ms intervals.

**Example:**
```
QCM09\t5d\t0\tC\t000394\t0.00020\t99.9\t09979727\t1.48871\t09979726.947\t1.48868\t09979726.901\t1.48873\t09979726.897\t1.48873\t09979726.927\t1.48868\t09979726.880\t99.9\t09992325\t1.41734\t09992324.788\t1.41732\t09992324.788\t1.41733\t09992324.762\t1.41730\t09992324.749\t1.41729\t09992324.758\t217\r\n
```

**Field map:**

| #    | Name           | Description                                    |
|------|----------------|------------------------------------------------|
| 0    | header         | "QCM09" — uppercase = long format              |
| 1    | hw_version     | "5d"                                           |
| 2    | status         | 0 = OK                                         |
| 3    | last_command   | Echo of last command                            |
| 4    | device_time    | Seconds since power-on                          |
| 5    | voltage_ux     | External voltage (V)                            |
| 6    | temp_a         | Temperature ch A                                |
| 7    | freq_a_int     | Integer frequency ch A                          |
| 8    | acg_a[0]       | ACG ch A at T₀                                 |
| 9    | freq_a[0]      | Precise freq ch A at T₀                        |
| 10   | acg_a[1]       | ACG ch A at T₀ + 0.2s                          |
| 11   | freq_a[1]      | Precise freq ch A at T₀ + 0.2s                 |
| 12   | acg_a[2]       | ACG ch A at T₀ + 0.4s                          |
| 13   | freq_a[2]      | Precise freq ch A at T₀ + 0.4s                 |
| 14   | acg_a[3]       | ACG ch A at T₀ + 0.6s                          |
| 15   | freq_a[3]      | Precise freq ch A at T₀ + 0.6s                 |
| 16   | acg_a[4]       | ACG ch A at T₀ + 0.8s                          |
| 17   | freq_a[4]      | Precise freq ch A at T₀ + 0.8s                 |
| 18   | temp_b         | Temperature ch B                                |
| 19   | freq_b_int     | Integer frequency ch B                          |
| 20   | acg_b[0]       | ACG ch B at T₀                                 |
| 21   | freq_b[0]      | Precise freq ch B at T₀                        |
| 22–27| ...            | (same pattern: acg, freq pairs for [1]–[3])    |
| 28   | acg_b[4]       | ACG ch B at T₀ + 0.8s                          |
| 29   | freq_b[4]      | Precise freq ch B at T₀ + 0.8s                 |
| 30   | checksum       | ASCII sum                                       |

### Checksum Calculation

Sum of all ASCII character values from the start of the line up to
**and including** the last TAB character before the checksum field.
CR and LF are excluded from the sum.

```python
def calculate_checksum(line: str) -> int:
    """Calculate checksum for a QCM data line.
    
    Sum all ASCII values from start up to and including
    the last tab before the checksum field.
    """
    # Find the last tab (before checksum)
    last_tab_pos = line.rstrip('\r\n').rfind('\t')
    payload = line[:last_tab_pos + 1]  # include the last tab
    return sum(ord(c) for c in payload)
```

### Format Detection

- Header starts with lowercase `qcm` → **short format** (1×/sec)
- Header starts with uppercase `QCM` → **long format** (5×/sec)

### Special Values

- Temperature `99.9` → sensor disconnected
- Status `0` → no error
- Voltage Ux range: 0–3.2V
