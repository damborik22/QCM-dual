# QCM-Dual Software — Master Development Plan

## How This Plan Works with Claude Code

This plan is designed around **Spec-Driven Development (SDD)** — the approach that
the Claude Code community has converged on as the most reliable way to build
production software with AI assistance. The key insight:

> **Review at phase gates, not during implementation.**
> Approve the spec upfront, then let Claude Code execute.

### Project Files Overview

```
qcm-dual/
├── CLAUDE.md              ← Claude Code reads this every session (project rules)
├── docs/
│   ├── PLAN.md            ← THIS FILE (overall strategy & phases)  
│   ├── SPEC.md            ← Detailed technical spec (data models, GUI layout, APIs)
│   └── PROTOCOL.md        ← Device protocol reference (commands, data formats)
├── .claude/
│   ├── commands/           ← Custom slash commands for recurring tasks
│   │   ├── implement.md   ← /project:implement — execute a phase
│   │   ├── test.md        ← /project:test — run and verify tests
│   │   └── review.md      ← /project:review — code review current changes
│   └── agents/            ← Custom subagents
│       ├── tester.md      ← Testing specialist
│       └── styler.md      ← UI/styling specialist
├── tests/
│   └── sample_data/       ← Real protocol data samples for testing
├── src/                   ← All application code (created during implementation)
└── pyproject.toml         ← Project metadata & dependencies
```

### Workflow Per Phase

```
You in Claude Code:

1. "/project:implement Phase N"
   → Claude reads SPEC.md, implements all files for that phase
   → Claude writes tests FIRST (TDD), then implementation
   → Claude commits after each logical unit

2. "/project:test"  
   → Claude runs pytest, fixes any failures
   → Claude verifies acceptance criteria from SPEC.md

3. "/project:review"
   → Claude reviews its own code as a staff engineer
   → Checks: type hints, docstrings, no GUI-thread blocking, signal/slot patterns

4. You verify visually (launch the app, click around)
   → If good → move to next phase
   → If not → tell Claude what to fix (tight feedback loop)
```

---

## Research Findings: What Works Best

### From the Claude Code Community (2025–2026)

**1. Spec-first, always.**
Practitioners consistently report that writing a detailed spec before any code
reduces rework by 50%+. The spec becomes the "source of truth" that Claude
can reference when context gets compacted. Our SPEC.md serves this role.

**2. Keep CLAUDE.md short (~50 rules max).**
Claude Code's system prompt already uses ~50 of the ~150–200 instruction budget
that LLMs can reliably follow. Our CLAUDE.md should contain only what Claude
would get wrong without it — not general Python style advice.

**3. Phase-gated implementation.**
Break the project into 5–7 phases, each independently testable. Never try to
build the whole app in one session. Each phase should be completable in one
Claude Code session (under ~50k tokens of context).

**4. TDD per phase.**
Write tests before implementation within each phase. This gives Claude a
concrete "done" signal and prevents regression in later phases.

**5. Use subagents for parallel independent work.**
When a phase has independent domains (e.g., "build the export module" and
"build the settings dialog"), use parallel subagents. But NEVER let two
subagents edit the same file.

**6. Commit often, /compact at 50%.**
After each logical unit (one module complete + tests pass), commit to git.
Use /compact proactively before context gets too large. Add standing instruction
in CLAUDE.md for what to preserve during compaction.

**7. Simulator-first development.**
Build and test against a mock/simulator before touching real hardware.
This is especially important for our QCM project — the simulator IS our
test harness.

**8. One session, one job.**
Don't try to fix bugs from Phase 2 while implementing Phase 5.
Start a fresh session for each phase. The spec file carries all context.

### From PySide6 / pyqtgraph Community

**9. Never block the GUI thread.**
All serial I/O in a QThread. Use Signal/Slot for all communication
between threads and GUI. This is the #1 source of bugs in Qt apps.

**10. pyqtgraph over matplotlib for live data.**
Matplotlib blocks; pyqtgraph is built on Qt's scene graph and handles
live streaming data natively. Use PlotWidget, not the matplotlib embed.

**11. QSS for theming.**
Define the entire theme as a single QSS string applied to QApplication.
Don't style individual widgets inline.

**12. PyInstaller needs testing early.**
Don't leave packaging to the last day. Do a test build after Phase 4
(when the app is functional) to catch hidden import issues.

---

## Phase Breakdown

### Phase 1: Foundation (Session 1)
**Goal:** Parser, data models, simulator, tests. No GUI.

**Why this first:** The protocol parser is the most critical and testable
component. Getting this right means everything downstream works.

**Deliverables:**
- `pyproject.toml` with all dependencies
- `src/core/data_models.py` — all dataclasses
- `src/core/protocol.py` — parse_short(), parse_long(), validate_checksum()
- `src/core/simulator.py` — generates realistic packets
- `tests/sample_data/` — exact examples from the manual
- `tests/test_protocol.py` — parsing, checksum, error cases
- `tests/test_simulator.py` — simulator output parses correctly

**Acceptance criteria:**
- [ ] `pytest tests/ -v` — all green
- [ ] parse_short() extracts all 14 fields correctly from sample
- [ ] parse_long() extracts 5 sub-measurements per channel
- [ ] Checksum validation works (true for valid, false for corrupted)
- [ ] Simulator packets pass through parser without error

**Prompt for Claude Code:**
```
Read docs/SPEC.md sections 3 and 7, and docs/PROTOCOL.md.
Implement Phase 1 from docs/PLAN.md.
Write tests FIRST using the sample data, then implement to pass them.
Commit after each module is complete with tests passing.
```

---

### Phase 2: Serial & Acquisition (Session 2)
**Goal:** SerialManager, AcquisitionEngine, connect to simulator.

**Deliverables:**
- `src/config.py` — QSettings wrapper with defaults
- `src/core/method.py` — Method dataclass, load/save `.qcm` JSON files
- `src/core/serial_manager.py` — QObject with signals, threaded reads
- `src/core/acquisition.py` — ring buffer, tare, derived values
- `tests/test_method.py`
- `tests/test_serial_manager.py`
- `tests/test_acquisition.py`

**Acceptance criteria:**
- [ ] SerialManager connects to simulator via "SIMULATOR" pseudo-port
- [ ] data_received signal fires with valid lines
- [ ] AcquisitionEngine produces MeasurementPoint from simulator
- [ ] Tare correctly zeros Δf for both channels
- [ ] Ring buffer stays bounded (no memory leak over 100k points)
- [ ] Commands are sent and echoed in packet's last_command field
- [ ] Method saves to / loads from `.qcm` JSON file correctly
- [ ] Method with default values round-trips without data loss

**Key design rule:** SerialManager owns ALL serial access. Nobody else
imports pyserial. The simulator plugs in at this level — it implements
the same read/write interface as a real serial port.

---

### Phase 3: GUI Shell (Session 3)
**Goal:** Window with all panels, dark theme. Static/placeholder data.

**Why static first:** Get the layout right before wiring live data.
Easier to iterate on appearance when you can just restart the app.

**Deliverables:**
- `src/gui/styles.py` — complete dark QSS theme
- `src/gui/main_window.py` — QMainWindow with all zones
- `src/gui/connection_panel.py` — port dropdown, connect button, LED
- `src/gui/control_panel.py` — all buttons, dropdowns, temp calibration buttons
- `src/gui/display_panel.py` — numeric readout cards
- `src/gui/plot_widget.py` — pyqtgraph with empty axes, legend, crosshair
- `src/main.py` — QApplication + theme + show window

**Acceptance criteria:**
- [ ] `python -m src.main` launches and shows the window
- [ ] Dark theme applied consistently to all widgets
- [ ] All 4 layout zones visible and properly proportioned
- [ ] Plot takes ~60% of vertical space
- [ ] Port dropdown lists "SIMULATOR" as an option
- [ ] All buttons render and are clickable (no-op is fine)
- [ ] Window resizes gracefully (plot stretches, panels stay fixed height)

**Subagent opportunity:** Use 2 parallel subagents:
- Agent 1: styles.py + display_panel.py + connection_panel.py + control_panel.py
- Agent 2: plot_widget.py + main_window.py layout

---

### Phase 4: Wire It Up (Session 4)
**Goal:** Simulator data flows live through all components to GUI.

This is the "magic moment" — simulated QCM data streaming in real-time.

**Deliverables:**
- Wire SerialManager → AcquisitionEngine → GUI signals
- ConnectionPanel triggers connect/disconnect
- ControlPanel triggers start/stop/single/mode/tare/temp calibration
- DisplayPanel updates from MeasurementPoint
- PlotWidget appends points, scrolls X axis
- Status bar: elapsed time, point count, errors, mode
- File menu: New/Open/Save Method (`.qcm` files)

**Acceptance criteria:**
- [ ] Select SIMULATOR → Connect → Start → see numbers updating at 1/sec
- [ ] Plot shows two colored lines (blue ch A, red ch B) scrolling
- [ ] Stop button stops updates; Start resumes
- [ ] Tare zeros Δf in display and plot
- [ ] Mode switch (1×/s ↔ 5×/s) changes update rate
- [ ] Status bar shows correct elapsed time and point count
- [ ] NO GUI freezing or lag (serial runs in thread)
- [ ] Disconnect → reconnect works cleanly
- [ ] Temperature calibration buttons send D/E/U/V commands
- [ ] Method Open loads `.qcm` and applies settings; Save persists them

**Test early with PyInstaller here!** Do a quick `pyinstaller --onefile src/main.py`
to catch import issues before spending more time on features.

---

### Phase 5: Processing & Export (Session 5)
**Goal:** Sauerbrey calculation, filters, CSV/XLSX/HDF5 export.

**Subagent opportunity:** 3 parallel subagents:
- Agent 1: `src/processing/sauerbrey.py` + `src/processing/filters.py` + tests
- Agent 2: `src/export/csv_export.py` + `src/export/excel_export.py` + `src/export/hdf5_export.py`
- Agent 3: `src/gui/settings_dialog.py` (Sauerbrey params, temp calibration, filter config)

**Deliverables:**
- Sauerbrey Δf → Δm conversion (configurable crystal params)
- Moving average + Savitzky-Golay filter
- Statistics: mean, std, drift rate
- CSV export with metadata header
- XLSX export (openpyxl)
- HDF5 export (h5py)
- Settings dialog for crystal parameters and temperature calibration
- File menu: Export CSV / XLSX / HDF5 with save dialog

**Acceptance criteria:**
- [ ] Δf of −10 Hz at 10 MHz → ~44.2 ng/cm² (matches published value)
- [ ] Filters smooth noisy simulator data (visual check)
- [ ] CSV opens correctly in Excel / pandas
- [ ] XLSX opens in LibreOffice without errors
- [ ] HDF5 round-trips: export → import → data matches
- [ ] All exports include metadata header
- [ ] Settings persist between app restarts (QSettings)

---

### Phase 6: Polish & Package (Session 6)
**Goal:** Error handling, keyboard shortcuts, icon, about dialog, .exe build.

**Deliverables:**
- Application icon (simple crystal + wave SVG)
- About dialog (version, author, device info)
- Keyboard shortcuts: Space=start/stop, T=tare, Ctrl+S=export
- Graceful error handling (no tracebacks to user)
- Window geometry save/restore
- `qcm_dual.spec` — PyInstaller spec file
- Final .exe tested on clean machine

**Acceptance criteria:**
- [ ] .exe starts without Python installed
- [ ] All features work in packaged form
- [ ] Serial disconnect shows user-friendly message, auto-reconnects
- [ ] Corrupted packets show warning in status bar, don't crash
- [ ] Settings persist between sessions
- [ ] About dialog shows correct version + device info

---

## CLAUDE.md (to place in project root)

```markdown
# QCM-Dual Control Software

Dual-channel QCM frequency meter control app.  
Python 3.11+ / PySide6 / pyqtgraph / pyserial.

## Read these first
- `docs/SPEC.md` — full technical specification (data models, GUI layout, APIs)
- `docs/PROTOCOL.md` — device communication protocol (commands, data formats)
- `docs/PLAN.md` — development phases and acceptance criteria

## Project layout
- `src/core/` — serial I/O, protocol parser, data models, simulator
- `src/processing/` — Sauerbrey, filters, statistics
- `src/gui/` — PySide6 widgets, main window, plots, styles
- `src/export/` — CSV, XLSX, HDF5
- `tests/` — pytest tests + sample data

## Build & run
- Install: `pip install -e ".[dev]"`
- Run: `python -m src.main`
- Test: `pytest tests/ -v`
- Single test: `pytest tests/test_protocol.py::test_parse_short -v`
- Build exe: `pyinstaller qcm_dual.spec`

## Rules
- Type hints on all function signatures
- Dataclasses for structured data, never raw dicts
- Qt Signals/Slots for ALL cross-component communication
- ALL serial I/O in QThread via SerialManager — never import pyserial elsewhere
- f-strings, pathlib, Google-style docstrings
- logger = logging.getLogger(__name__) in every module
- Channel A = blue (#4fc3f7), Channel B = red (#ef5350) everywhere
- Frequency values: float in Hz. Mass: float in ng/cm²
- Temp 99.9 means "sensor disconnected" — display as "---"

## When compacting
Preserve: current phase being implemented, list of completed/remaining files,
any failing test details, the acceptance criteria for current phase.

## Testing
- Write tests FIRST, then implement to pass them
- Use sample data from tests/sample_data/ for protocol tests
- Use simulator for integration tests (connect to "SIMULATOR" port)
```

---

## Custom Commands

### `.claude/commands/implement.md`
```markdown
---
description: Implement a specific phase from the development plan
argument-hint: "Phase N"
---

Read docs/PLAN.md and docs/SPEC.md.
Implement the requested phase following these rules:

1. Read the acceptance criteria for the phase
2. Write ALL tests first (TDD)
3. Implement code to make tests pass
4. Run `pytest tests/ -v` to verify
5. Commit after each module with passing tests
6. After all files done, verify ALL acceptance criteria

Do not implement anything beyond the current phase.
If you need context from a previous phase, read the existing source files.
```

### `.claude/commands/test.md`
```markdown
---
description: Run tests and fix any failures
---

1. Run `pytest tests/ -v`
2. If any tests fail:
   - Read the failing test to understand what's expected
   - Read the implementation being tested
   - Fix the implementation (not the test, unless the test is wrong)
   - Re-run until all pass
3. Report: total tests, passed, failed, and any remaining issues
```

### `.claude/commands/review.md`
```markdown
---
description: Review code changes like a staff engineer
---

Review all modified files in this session. Check:

1. Type hints on all function signatures?
2. Docstrings on all public classes and methods?
3. No serial I/O outside SerialManager?
4. No blocking calls in GUI thread?
5. All Signal/Slot connections correct?
6. Dataclasses used (no raw dicts for structured data)?
7. Logger in every module?
8. Consistent color scheme (A=blue, B=red)?
9. Error handling: no bare except, user-friendly messages
10. Does the code match the spec in docs/SPEC.md?

Report issues as a numbered list. Fix critical issues.
```

---

## Custom Subagents

### `.claude/agents/tester.md`
```markdown
---
name: tester
description: Testing specialist. Use for writing and fixing pytest tests.
tools: Read, Edit, Bash
---

You are a testing specialist for a Python/PySide6 scientific instrument app.

When writing tests:
- Use pytest with descriptive test names
- Use sample data from tests/sample_data/ for protocol tests
- Use parametrize for multiple input cases
- Mock serial ports, don't use real hardware
- For GUI tests, only test that widgets exist and signals are wired (no visual tests)

When fixing tests:
- Read the test first to understand intent
- Fix implementation, not test (unless test is clearly wrong)
- Run only the specific failing test with -v flag
```

### `.claude/agents/styler.md`
```markdown
---
name: styler
description: UI and styling specialist for PySide6/QSS dark theme.
tools: Read, Edit, Bash
---

You are a UI specialist for a PySide6 scientific instrument app.

Design system:
- Background: #1e1e2e (dark blue-gray)
- Surface: #2a2a3d, border: 1px #3a3a5c, radius: 8px
- Text: #e0e0e0 primary, #8888aa secondary
- Blue accent: #4fc3f7 (channel A, interactive elements)
- Red accent: #ef5350 (channel B)
- Green: #66bb6a (connected/OK)
- Amber: #ffa726 (warnings)
- Monospace font for numeric values, system default for labels
- Plot bg: #1a1a2e, grid: #2a2a4a

Write QSS that is clean and minimal. No inline styles on widgets.
```

---

## Tips for You (the Human)

1. **Start each session with:** `Read docs/PLAN.md and docs/SPEC.md`
   to give Claude full context.

2. **One phase per session.** Start fresh (`/clear`) between phases.
   The spec files carry all context.

3. **After Phase 4, test PyInstaller immediately.** Hidden import
   issues are easier to fix with a working app than a finished one.

4. **If Claude drifts:** say "Check docs/SPEC.md section X" to
   re-anchor it on the spec.

5. **Visual issues are best fixed with tight feedback:**
   "The plot area is too small, it should take 60% of the window height.
   The display cards should be fixed at 120px height."

6. **Don't skip the review command.** Run `/project:review` after each
   phase. It catches threading bugs and missing type hints early.
