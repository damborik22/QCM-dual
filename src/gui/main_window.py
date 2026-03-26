"""Main application window for QCM-Dual.

Assembles all GUI zones (connection, control, display, plot) into a
single QMainWindow with menu bar and status bar.
"""
import logging

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.gui.connection_panel import ConnectionPanel
from src.gui.control_panel import ControlPanel
from src.gui.display_panel import DisplayPanel
from src.gui.plot_widget import PlotPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for QCM-Dual control software.

    Organizes the UI into four horizontal zones:
        Zone 1: Connection panel (left) + Control panel (right)
        Zone 2: Display panel (numeric readout cards)
        Zone 3: Plot panel (pyqtgraph, stretches to fill)
        Zone 4: Status bar

    Attributes:
        connection_panel: ConnectionPanel widget.
        control_panel: ControlPanel widget.
        display_panel: DisplayPanel widget.
        plot_panel: PlotPanel widget.
        elapsed_label: Status bar label for elapsed time.
        points_label: Status bar label for point count.
        errors_label: Status bar label for error count.
        voltage_label: Status bar label for external voltage.
        mode_label: Status bar label for measurement rate mode.
        connection_label: Status bar label for connection state.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("QCM-Dual")
        self.setMinimumSize(1024, 700)

        # Central widget and main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 4)
        main_layout.setSpacing(6)

        # Zone 1: Connection + Control
        zone1 = self._create_zone1()
        main_layout.addWidget(zone1)

        # Zone 2: Display panel
        self.display_panel = DisplayPanel()
        self.display_panel.setFixedHeight(160)
        main_layout.addWidget(self.display_panel)

        # Zone 3: Plot panel
        self.plot_panel = PlotPanel()
        self.plot_panel.setMinimumHeight(300)
        main_layout.addWidget(self.plot_panel, stretch=1)

        # Zone 4: Status bar
        self._create_status_bar()

        # Menu bar
        self._create_menu_bar()

        # Wire reference channel selector
        self.control_panel.ref_combo.currentTextChanged.connect(
            self._on_reference_changed
        )

        logger.info("MainWindow initialized")

    # ------------------------------------------------------------------
    # Zone 1: Connection + Control
    # ------------------------------------------------------------------

    def _create_zone1(self) -> QFrame:
        """Build Zone 1 containing ConnectionPanel and ControlPanel.

        Returns:
            QFrame with horizontal layout.
        """
        frame = QFrame()
        frame.setObjectName("zone1Frame")
        frame.setFixedHeight(80)
        hbox = QHBoxLayout(frame)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(8)

        self.connection_panel = ConnectionPanel()
        hbox.addWidget(self.connection_panel)

        hbox.addStretch()

        self.control_panel = ControlPanel()
        hbox.addWidget(self.control_panel)

        return frame

    # ------------------------------------------------------------------
    # Status bar (Zone 4)
    # ------------------------------------------------------------------

    def _create_status_bar(self) -> None:
        """Build the status bar with permanent indicator widgets."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.elapsed_label = QLabel("\u23f1 00:00:00")
        self.elapsed_label.setObjectName("statusElapsed")
        status_bar.addPermanentWidget(self.elapsed_label)

        self.points_label = QLabel("Points: 0")
        self.points_label.setObjectName("statusPoints")
        status_bar.addPermanentWidget(self.points_label)

        self.errors_label = QLabel("Errors: 0")
        self.errors_label.setObjectName("statusErrors")
        status_bar.addPermanentWidget(self.errors_label)

        self.voltage_label = QLabel("Ux: 0.00000 V")
        self.voltage_label.setObjectName("statusVoltage")
        status_bar.addPermanentWidget(self.voltage_label)

        self.mode_label = QLabel("1\u00d7/s")
        self.mode_label.setObjectName("statusMode")
        status_bar.addPermanentWidget(self.mode_label)

        self.connection_label = QLabel("Disconnected")
        self.connection_label.setObjectName("statusConnection")
        status_bar.addPermanentWidget(self.connection_label)

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _create_menu_bar(self) -> None:
        """Build the application menu bar with all menus and actions."""
        menubar = self.menuBar()

        # -- File menu --
        file_menu = menubar.addMenu("&File")

        self.action_new_method = QAction("New Method", self)
        file_menu.addAction(self.action_new_method)

        self.action_open_method = QAction("Open Method...", self)
        self.action_open_method.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addAction(self.action_open_method)

        self.action_save_method = QAction("Save Method", self)
        self.action_save_method.setShortcut(QKeySequence.StandardKey.Save)
        file_menu.addAction(self.action_save_method)

        self.action_save_method_as = QAction("Save Method As...", self)
        self.action_save_method_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        file_menu.addAction(self.action_save_method_as)

        file_menu.addSeparator()

        self.recent_methods_menu = QMenu("Recent Methods", self)
        file_menu.addMenu(self.recent_methods_menu)

        file_menu.addSeparator()

        self.action_export_csv = QAction("Export CSV", self)
        file_menu.addAction(self.action_export_csv)

        self.action_export_xlsx = QAction("Export XLSX", self)
        file_menu.addAction(self.action_export_xlsx)

        self.action_export_hdf5 = QAction("Export HDF5", self)
        file_menu.addAction(self.action_export_hdf5)

        file_menu.addSeparator()

        self.action_exit = QAction("Exit", self)
        self.action_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)

        # -- Device menu --
        device_menu = menubar.addMenu("&Device")

        self.action_connect = QAction("Connect", self)
        device_menu.addAction(self.action_connect)

        self.action_disconnect = QAction("Disconnect", self)
        device_menu.addAction(self.action_disconnect)

        device_menu.addSeparator()

        self.action_simulator_mode = QAction("Simulator mode", self)
        self.action_simulator_mode.setCheckable(True)
        device_menu.addAction(self.action_simulator_mode)

        device_menu.addSeparator()

        self.action_device_settings = QAction("Device settings...", self)
        device_menu.addAction(self.action_device_settings)

        device_menu.addSeparator()

        self.action_send_command = QAction("Send command...", self)
        device_menu.addAction(self.action_send_command)

        # -- View menu --
        view_menu = menubar.addMenu("&View")

        self.action_show_connection = QAction("Show/hide Connection panel", self)
        self.action_show_connection.setCheckable(True)
        self.action_show_connection.setChecked(True)
        view_menu.addAction(self.action_show_connection)

        self.action_show_control = QAction("Show/hide Control panel", self)
        self.action_show_control.setCheckable(True)
        self.action_show_control.setChecked(True)
        view_menu.addAction(self.action_show_control)

        view_menu.addSeparator()

        self.action_display_all = QAction("Display: All channels", self)
        self.action_display_all.setCheckable(True)
        self.action_display_all.setChecked(True)
        view_menu.addAction(self.action_display_all)

        self.action_display_diff = QAction("Display: Differential only", self)
        self.action_display_diff.setCheckable(True)
        view_menu.addAction(self.action_display_diff)

        view_menu.addSeparator()

        self.action_reset_layout = QAction("Reset layout", self)
        view_menu.addAction(self.action_reset_layout)

        # -- Tools menu --
        tools_menu = menubar.addMenu("&Tools")

        self.action_sauerbrey = QAction("Sauerbrey settings", self)
        tools_menu.addAction(self.action_sauerbrey)

        self.action_temp_cal = QAction("Temperature calibration", self)
        tools_menu.addAction(self.action_temp_cal)

        self.action_statistics = QAction("Statistics", self)
        tools_menu.addAction(self.action_statistics)

        # -- Help menu --
        help_menu = menubar.addMenu("&Help")

        self.action_about = QAction("About", self)
        help_menu.addAction(self.action_about)

        logger.debug("Menu bar created")

    # ------------------------------------------------------------------
    # Reference channel handling
    # ------------------------------------------------------------------

    def _on_reference_changed(self, ref: str) -> None:
        """Handle reference channel combo change.

        Updates the display panel (show/hide diff card) and enables/disables
        the diff trace toggle buttons in the plot panel.

        Args:
            ref: "None", "Ch A", or "Ch B".
        """
        self.display_panel.set_reference_channel(ref)

        has_ref = ref != "None"
        for key in ("delta_f_diff", "delta_m_diff"):
            btn = self.plot_panel.toggle_buttons.get(key)
            if btn is not None:
                btn.setEnabled(has_ref)
                if not has_ref:
                    btn.setChecked(False)

        logger.info("Reference channel changed to: %s", ref)
