"""Plot panel with pyqtgraph PlotWidget, toolbar, and crosshair.

Provides real-time plotting of QCM measurement data with dual Y-axis
support, per-channel lines, and a coordinate-readout crosshair.
"""
import logging

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)

# Y-axis combo items
Y1_ITEMS: list[str] = [
    "\u0394f",
    "Frequency",
    "\u0394m",
    "ACG",
    "Temperature",
    "\u0394f (A\u2212B)",
    "\u0394m (A\u2212B)",
]

Y2_ITEMS: list[str] = [
    "None",
    "\u0394f",
    "Frequency",
    "\u0394m",
    "ACG",
    "Temperature",
    "\u0394f (A\u2212B)",
    "\u0394m (A\u2212B)",
]

# Units for each parameter
_UNITS: dict[str, str] = {
    "\u0394f": "Hz",
    "Frequency": "Hz",
    "\u0394m": "ng/cm\u00b2",
    "ACG": "V",
    "Temperature": "\u00b0C",
    "\u0394f (A\u2212B)": "Hz",
    "\u0394m (A\u2212B)": "ng/cm\u00b2",
}

# Channel colors
COLOR_A = "#4fc3f7"
COLOR_B = "#ef5350"
COLOR_DIFF = "#66bb6a"
COLOR_CROSSHAIR = "#888888"

# Plot styling
PLOT_BG = "#1a1a2e"
GRID_COLOR = (42, 42, 74, 128)  # #2a2a4a with alpha ~0.5


class PlotPanel(QFrame):
    """Plot panel containing a toolbar and a pyqtgraph PlotWidget.

    Attributes:
        y1_combo: QComboBox for left Y-axis parameter selection.
        y2_combo: QComboBox for right Y-axis parameter selection.
        tare_btn: QPushButton to tare channels.
        autoscale_btn: QPushButton to autoscale axes.
        clear_btn: QPushButton to clear all plot data.
        plot_widget: The pyqtgraph PlotWidget instance.
        line_a: PlotDataItem for channel A.
        line_b: PlotDataItem for channel B.
        line_diff: PlotDataItem for differential (A-B), initially hidden.
        crosshair_label: QLabel showing crosshair coordinates.
    """

    tare_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PlotPanel")
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # -- Toolbar --
        self._toolbar = self._create_toolbar()
        layout.addWidget(self._toolbar)

        # -- Plot widget --
        self.plot_widget = pg.PlotWidget()
        self._configure_plot()
        layout.addWidget(self.plot_widget, stretch=1)

        # -- Crosshair coordinate label --
        self.crosshair_label = QLabel("")
        self.crosshair_label.setObjectName("crosshairLabel")
        self.crosshair_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.crosshair_label)

        # -- Data lines --
        self.line_a = self.plot_widget.plot(
            [], [], pen=pg.mkPen(COLOR_A, width=2), name="Ch A"
        )
        self.line_b = self.plot_widget.plot(
            [], [], pen=pg.mkPen(COLOR_B, width=2), name="Ch B"
        )
        self.line_diff = self.plot_widget.plot(
            [], [], pen=pg.mkPen(COLOR_DIFF, width=2), name="Diff (A\u2212B)"
        )
        self.line_diff.setVisible(False)

        # -- Right Y axis (ViewBox) --
        self._right_vb = pg.ViewBox()
        self.plot_widget.scene().addItem(self._right_vb)
        self.plot_widget.getAxis("right").linkToView(self._right_vb)
        self._right_vb.setXLink(self.plot_widget.getPlotItem())
        self.plot_widget.getAxis("right").setLabel("")
        self.plot_widget.getAxis("right").hide()

        # Lines for the right axis (initially empty and hidden)
        self.line_a_r = pg.PlotDataItem(
            [], [], pen=pg.mkPen(COLOR_A, width=2, style=Qt.PenStyle.DashLine)
        )
        self.line_b_r = pg.PlotDataItem(
            [], [], pen=pg.mkPen(COLOR_B, width=2, style=Qt.PenStyle.DashLine)
        )
        self.line_diff_r = pg.PlotDataItem(
            [], [], pen=pg.mkPen(COLOR_DIFF, width=2, style=Qt.PenStyle.DashLine)
        )
        self._right_vb.addItem(self.line_a_r)
        self._right_vb.addItem(self.line_b_r)
        self._right_vb.addItem(self.line_diff_r)
        self.line_a_r.setVisible(False)
        self.line_b_r.setVisible(False)
        self.line_diff_r.setVisible(False)

        # Keep right ViewBox geometry in sync
        self.plot_widget.getPlotItem().vb.sigResized.connect(self._update_right_vb)

        # -- Crosshair --
        self._crosshair_v = pg.InfiniteLine(
            angle=90, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1)
        )
        self._crosshair_h = pg.InfiniteLine(
            angle=0, movable=False, pen=pg.mkPen(COLOR_CROSSHAIR, width=1)
        )
        self.plot_widget.addItem(self._crosshair_v, ignoreBounds=True)
        self.plot_widget.addItem(self._crosshair_h, ignoreBounds=True)

        # Mouse tracking for crosshair
        self._proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._on_mouse_moved,
        )

        # -- Legend --
        self._legend = self.plot_widget.addLegend(
            offset=(10, 10),
            labelTextColor="#e0e0e0",
            brush=pg.mkBrush(42, 42, 61, 180),
            pen=pg.mkPen("#3a3a5c"),
        )

        # Wire up toolbar signals
        self.y1_combo.currentIndexChanged.connect(self._on_y1_changed)
        self.y2_combo.currentIndexChanged.connect(self._on_y2_changed)
        self.tare_btn.clicked.connect(self.tare_requested.emit)
        self.autoscale_btn.clicked.connect(self._on_autoscale)
        self.clear_btn.clicked.connect(self.clear_requested.emit)

        # Set initial axis label
        self._on_y1_changed()

        logger.info("PlotPanel initialized")

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _create_toolbar(self) -> QFrame:
        """Build the horizontal toolbar above the plot.

        Returns:
            QFrame containing all toolbar widgets.
        """
        toolbar = QFrame()
        toolbar.setObjectName("plotToolbar")
        toolbar.setFixedHeight(36)
        hbox = QHBoxLayout(toolbar)
        hbox.setContentsMargins(8, 2, 8, 2)
        hbox.setSpacing(8)

        # Y1 selector
        y1_label = QLabel("Y1:")
        y1_label.setObjectName("toolbarLabel")
        hbox.addWidget(y1_label)

        self.y1_combo = QComboBox()
        self.y1_combo.setObjectName("y1_combo")
        self.y1_combo.addItems(Y1_ITEMS)
        self.y1_combo.setCurrentIndex(0)  # Default: delta-f
        hbox.addWidget(self.y1_combo)

        # Y2 selector
        y2_label = QLabel("Y2:")
        y2_label.setObjectName("toolbarLabel")
        hbox.addWidget(y2_label)

        self.y2_combo = QComboBox()
        self.y2_combo.setObjectName("y2_combo")
        self.y2_combo.addItems(Y2_ITEMS)
        self.y2_combo.setCurrentIndex(0)  # Default: "None"
        hbox.addWidget(self.y2_combo)

        hbox.addStretch()

        # Action buttons
        self.tare_btn = QPushButton("Tare")
        self.tare_btn.setObjectName("tare_btn")
        hbox.addWidget(self.tare_btn)

        self.autoscale_btn = QPushButton("Autoscale")
        self.autoscale_btn.setObjectName("autoscale_btn")
        hbox.addWidget(self.autoscale_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clear_btn")
        hbox.addWidget(self.clear_btn)

        return toolbar

    # ------------------------------------------------------------------
    # Plot configuration
    # ------------------------------------------------------------------

    def _configure_plot(self) -> None:
        """Apply styling and axis configuration to the plot widget."""
        self.plot_widget.setBackground(PLOT_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.5)

        for axis_name in ("bottom", "left", "right"):
            axis = self.plot_widget.getAxis(axis_name)
            axis.setGrid(128)  # alpha handled by showGrid
            axis.setTextPen("#e0e0e0")
            axis.setPen("#3a3a5c")

        # Axis labels
        self.plot_widget.setLabel("bottom", "Time (s)", color="#8888aa")
        self.plot_widget.setLabel("left", "\u0394f (Hz)", color="#8888aa")

        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange()

    # ------------------------------------------------------------------
    # Right ViewBox sync
    # ------------------------------------------------------------------

    def _update_right_vb(self) -> None:
        """Synchronize right ViewBox geometry with the main plot area."""
        self._right_vb.setGeometry(
            self.plot_widget.getPlotItem().vb.sceneBoundingRect()
        )
        self._right_vb.linkedViewChanged(
            self.plot_widget.getPlotItem().vb, self._right_vb.XAxis
        )

    # ------------------------------------------------------------------
    # Axis label updates
    # ------------------------------------------------------------------

    def _on_y1_changed(self) -> None:
        """Update left Y-axis label when Y1 selection changes."""
        text = self.y1_combo.currentText()
        unit = _UNITS.get(text, "")
        label = f"{text} ({unit})" if unit else text
        self.plot_widget.setLabel("left", label, color="#8888aa")
        logger.debug("Y1 axis changed to: %s", text)

    def _on_y2_changed(self) -> None:
        """Update right Y-axis visibility and label when Y2 selection changes."""
        text = self.y2_combo.currentText()
        if text == "None":
            self.plot_widget.getAxis("right").hide()
            self.line_a_r.setVisible(False)
            self.line_b_r.setVisible(False)
            self.line_diff_r.setVisible(False)
            logger.debug("Y2 axis hidden")
        else:
            unit = _UNITS.get(text, "")
            label = f"{text} ({unit})" if unit else text
            self.plot_widget.getAxis("right").setLabel(label, color="#8888aa")
            self.plot_widget.getAxis("right").show()
            logger.debug("Y2 axis changed to: %s", text)

    # ------------------------------------------------------------------
    # Crosshair
    # ------------------------------------------------------------------

    def _on_mouse_moved(self, event: tuple) -> None:
        """Update crosshair position and coordinate label.

        Args:
            event: Tuple containing the mouse position QPointF.
        """
        pos = event[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()
            self._crosshair_v.setPos(x)
            self._crosshair_h.setPos(y)
            self.crosshair_label.setText(f"  x = {x:.2f} s   y = {y:.4f}")

    # ------------------------------------------------------------------
    # Autoscale
    # ------------------------------------------------------------------

    def _on_autoscale(self) -> None:
        """Reset plot to auto-range on all axes."""
        self.plot_widget.enableAutoRange()
        self._right_vb.enableAutoRange()
        logger.debug("Autoscale triggered")
