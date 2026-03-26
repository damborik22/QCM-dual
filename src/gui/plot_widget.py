"""Plot panel with pyqtgraph PlotWidget and trace toggle toolbar.

Provides real-time plotting of QCM measurement data. Users click toggle
buttons to show/hide individual traces on the plot.
"""
import logging

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)

# Channel colors
COLOR_A = "#4fc3f7"
COLOR_B = "#ef5350"
COLOR_DIFF = "#66bb6a"
COLOR_MASS = "#ab47bc"
COLOR_TEMP_A = "#26c6da"
COLOR_TEMP_B = "#ffa726"
COLOR_CROSSHAIR = "#888888"

# Plot styling
PLOT_BG = "#1a1a2e"

# Trace definitions: (key, label, channel, color, unit, default_on)
# Diff direction is determined by the Reference channel selector in ControlPanel.
TRACE_DEFS: list[tuple[str, str, str, str, str, bool]] = [
    ("freq_a",       "Freq A",  "A",    COLOR_A,    "Hz",           True),
    ("freq_b",       "Freq B",  "B",    COLOR_B,    "Hz",           True),
    ("delta_f_diff", "\u0394f", "Diff", COLOR_DIFF, "Hz",           False),
    ("delta_m_diff", "\u0394m", "Diff", COLOR_MASS, "ng/cm\u00b2",  False),
    ("temp_a",       "Temp A",  "A",    COLOR_TEMP_A, "\u00b0C",    False),
    ("temp_b",       "Temp B",  "B",    COLOR_TEMP_B, "\u00b0C",    False),
]

# Separators between groups (insert after these indices in TRACE_DEFS)
_GROUP_BREAKS = {1, 3}  # after Freq B, Δm Diff


class _TraceToggle(QPushButton):
    """Checkable button for toggling a plot trace."""

    def __init__(self, key: str, label: str, color: str, parent: "QFrame | None" = None) -> None:
        super().__init__(label, parent)
        self.key = key
        self._color = color
        self.setCheckable(True)
        self.setFixedHeight(26)
        self._update_style()
        self.toggled.connect(lambda _: self._update_style())

    def _update_style(self) -> None:
        """Update button appearance based on checked state."""
        if self.isChecked():
            self.setStyleSheet(
                f"QPushButton {{ background: {self._color}; color: #1e1e2e; "
                f"border: 2px solid {self._color}; border-radius: 4px; "
                f"padding: 2px 8px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: {self._color}; }}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton {{ background: #2a2a3d; color: {self._color}; "
                f"border: 1px solid #3a3a5c; border-radius: 4px; "
                f"padding: 2px 8px; }}"
                f"QPushButton:hover {{ border-color: {self._color}; }}"
            )


class PlotPanel(QFrame):
    """Plot panel with trace toggle toolbar and pyqtgraph PlotWidget.

    Attributes:
        tare_btn: QPushButton to tare channels.
        autoscale_btn: QPushButton to autoscale axes.
        clear_btn: QPushButton to clear all plot data.
        plot_widget: The pyqtgraph PlotWidget instance.
        traces: Dict mapping trace key to PlotDataItem.
        toggle_buttons: Dict mapping trace key to _TraceToggle button.
        crosshair_label: QLabel showing crosshair coordinates.
    """

    tare_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PlotPanel")
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.traces: dict[str, pg.PlotDataItem] = {}
        self.toggle_buttons: dict[str, _TraceToggle] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar with toggle buttons
        self._toolbar = self._create_toolbar()
        layout.addWidget(self._toolbar)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self._configure_plot()
        layout.addWidget(self.plot_widget, stretch=1)

        # Crosshair coordinate label
        self.crosshair_label = QLabel("")
        self.crosshair_label.setObjectName("crosshairLabel")
        self.crosshair_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.crosshair_label)

        # Create data lines for each trace
        self._create_traces()

        # Diff toggles disabled until a reference channel is selected
        for key in ("delta_f_diff", "delta_m_diff"):
            if key in self.toggle_buttons:
                self.toggle_buttons[key].setEnabled(False)

        # Crosshair
        self._crosshair_v = pg.InfiniteLine(
            angle=90, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1)
        )
        self._crosshair_h = pg.InfiniteLine(
            angle=0, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1)
        )
        self.plot_widget.addItem(self._crosshair_v, ignoreBounds=True)
        self.plot_widget.addItem(self._crosshair_h, ignoreBounds=True)

        self._proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._on_mouse_moved,
        )

        # Legend
        self._legend = self.plot_widget.addLegend(
            offset=(10, 10),
            labelTextColor="#e0e0e0",
            brush=pg.mkBrush(42, 42, 61, 180),
            pen=pg.mkPen("#3a3a5c"),
        )

        # Recording region highlights (semi-transparent red bands)
        self._record_regions: list[pg.LinearRegionItem] = []
        self._active_region: pg.LinearRegionItem | None = None

        # Wire action buttons
        self.tare_btn.clicked.connect(self.tare_requested.emit)
        self.autoscale_btn.clicked.connect(self._on_autoscale)
        self.clear_btn.clicked.connect(self.clear_requested.emit)

        logger.info("PlotPanel initialized")

    def _create_toolbar(self) -> QFrame:
        """Build toolbar with trace toggle buttons and action buttons."""
        toolbar = QFrame()
        toolbar.setObjectName("plotToolbar")
        toolbar.setFixedHeight(36)
        hbox = QHBoxLayout(toolbar)
        hbox.setContentsMargins(8, 2, 8, 2)
        hbox.setSpacing(4)

        for i, (key, label, _ch, color, _unit, default_on) in enumerate(TRACE_DEFS):
            btn = _TraceToggle(key, label, color)
            btn.setChecked(default_on)
            btn.toggled.connect(self._on_trace_toggled)
            self.toggle_buttons[key] = btn
            hbox.addWidget(btn)

            if i in _GROUP_BREAKS:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet("color: #3a3a5c;")
                sep.setFixedWidth(2)
                hbox.addWidget(sep)

        hbox.addStretch()

        # Action buttons
        self.tare_btn = QPushButton("Tare")
        self.autoscale_btn = QPushButton("Autoscale")
        self.clear_btn = QPushButton("Clear")

        for btn in (self.tare_btn, self.autoscale_btn, self.clear_btn):
            hbox.addWidget(btn)

        return toolbar

    def _configure_plot(self) -> None:
        """Apply styling and axis configuration."""
        self.plot_widget.setBackground(PLOT_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.5)

        for axis_name in ("bottom", "left"):
            axis = self.plot_widget.getAxis(axis_name)
            axis.setTextPen("#e0e0e0")
            axis.setPen("#3a3a5c")

        self.plot_widget.setLabel("bottom", "Time (s)", color="#8888aa")
        self.plot_widget.setLabel("left", "", color="#8888aa")
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange()

    def _create_traces(self) -> None:
        """Create PlotDataItem for each trace definition."""
        for key, label, _ch, color, _unit, default_on in TRACE_DEFS:
            line = self.plot_widget.plot(
                [], [],
                pen=pg.mkPen(color, width=2),
                name=label,
            )
            line.setVisible(default_on)
            self.traces[key] = line

    def _on_trace_toggled(self, checked: bool) -> None:
        """Show/hide trace when toggle button is clicked."""
        btn = self.sender()
        if btn is None:
            return
        key = btn.key
        if key in self.traces:
            self.traces[key].setVisible(checked)
            logger.debug("Trace %s: %s", key, "shown" if checked else "hidden")

        # Update Y-axis label based on visible traces
        self._update_axis_label()

    def _update_axis_label(self) -> None:
        """Set Y-axis label with units colored to match their traces.

        Each visible trace contributes its own colored unit label,
        so the same unit (e.g. Hz) can appear multiple times in
        different colors when multiple channels are shown.
        """
        parts: list[str] = []
        seen: set[tuple[str, str]] = set()  # (unit, color) dedup
        for key, label, _ch, color, unit, _default in TRACE_DEFS:
            if key in self.toggle_buttons and self.toggle_buttons[key].isChecked():
                pair = (unit, color)
                if pair not in seen:
                    seen.add(pair)
                    parts.append(
                        f'<span style="color:{color}">{unit}</span>'
                    )

        if not parts:
            self.plot_widget.setLabel("left", "", color="#8888aa")
        else:
            self.plot_widget.getAxis("left").setLabel(" &nbsp; ".join(parts))

    def switch_to_diff(self) -> None:
        """Auto-switch plot view from raw frequencies to differential.

        Called when Tare is pressed. Turns off Freq A/B, turns on Δf Diff.
        """
        for key in ("freq_a", "freq_b"):
            if key in self.toggle_buttons:
                self.toggle_buttons[key].setChecked(False)
        if "delta_f_diff" in self.toggle_buttons:
            self.toggle_buttons["delta_f_diff"].setChecked(True)
        logger.info("Plot switched to differential view")

    def switch_to_freq(self) -> None:
        """Switch plot view back to raw frequencies.

        Turns off diff traces, turns on Freq A/B.
        """
        for key in ("delta_f_diff", "delta_m_diff"):
            if key in self.toggle_buttons:
                self.toggle_buttons[key].setChecked(False)
        for key in ("freq_a", "freq_b"):
            if key in self.toggle_buttons:
                self.toggle_buttons[key].setChecked(True)
        logger.info("Plot switched to frequency view")

    def start_recording_region(self, start_time: float) -> None:
        """Create a new recording highlight starting at the given time.

        Args:
            start_time: Elapsed time (seconds) where recording begins.
        """
        region = pg.LinearRegionItem(
            values=[start_time, start_time],
            orientation="vertical",
            movable=False,
            brush=pg.mkBrush(198, 40, 40, 40),
            pen=pg.mkPen("#c62828", width=1),
        )
        self.plot_widget.addItem(region, ignoreBounds=True)
        self._record_regions.append(region)
        self._active_region = region

    def update_recording_region(self, end_time: float) -> None:
        """Extend the active recording highlight to the current time.

        Args:
            end_time: Elapsed time (seconds) for the right edge.
        """
        if self._active_region is not None:
            start = self._active_region.getRegion()[0]
            self._active_region.setRegion([start, end_time])

    def stop_recording_region(self) -> None:
        """Freeze the active recording highlight. It stays visible."""
        self._active_region = None

    def clear_recording_region(self) -> None:
        """Remove all recording highlights."""
        for region in self._record_regions:
            self.plot_widget.removeItem(region)
        self._record_regions.clear()
        self._active_region = None

    def get_visible_trace_keys(self) -> list[str]:
        """Return list of currently visible trace keys.

        Returns:
            List of trace key strings that are toggled on.
        """
        return [key for key, btn in self.toggle_buttons.items() if btn.isChecked()]

    def _on_mouse_moved(self, event: tuple) -> None:
        """Update crosshair position and coordinate label."""
        pos = event[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()
            self._crosshair_v.setPos(x)
            self._crosshair_h.setPos(y)
            self.crosshair_label.setText(f"  x = {x:.2f} s   y = {y:.4f}")

    def _on_autoscale(self) -> None:
        """Reset plot to auto-range."""
        self.plot_widget.enableAutoRange()
        logger.debug("Autoscale triggered")
