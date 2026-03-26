"""Dark theme QSS stylesheet and color constants for QCM-Dual application.

All widget styling is defined here as a single QSS string (DARK_THEME)
applied via QApplication.setStyleSheet(). Individual widgets must NOT
use inline setStyleSheet() calls.
"""
import logging
import sys

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform-aware monospace font
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    MONO_FONT = "Consolas"
else:
    MONO_FONT = "monospace"

# ---------------------------------------------------------------------------
# Color constants — importable by any module that needs programmatic colors
# (e.g. pyqtgraph pen colors, QPalette tweaks).
# ---------------------------------------------------------------------------
COLOR_BG = "#1e1e2e"
COLOR_SURFACE = "#2a2a3d"
COLOR_SURFACE_BORDER = "#3a3a5c"
COLOR_INPUT = "#353550"
COLOR_TEXT_PRIMARY = "#e0e0e0"
COLOR_TEXT_SECONDARY = "#8888aa"
COLOR_A = "#4fc3f7"          # Channel A (blue)
COLOR_B = "#ef5350"          # Channel B (red)
COLOR_DIFF = "#66bb6a"       # Differential / connected / OK (green)
COLOR_GREEN = "#66bb6a"
COLOR_AMBER = "#ffa726"
COLOR_BTN_BG = "#353550"
COLOR_BTN_HOVER = "#454570"
COLOR_DISABLED_TEXT = "#555555"
COLOR_DISABLED_BG = "#2a2a3d"
COLOR_PLOT_BG = "#1a1a2e"
COLOR_PLOT_GRID = "#2a2a4a"
COLOR_SCROLLBAR = "#3a3a5c"

# ---------------------------------------------------------------------------
# Master QSS — applied once at startup via app.setStyleSheet(DARK_THEME)
# ---------------------------------------------------------------------------
DARK_THEME = f"""
/* ================================================================
   QCM-Dual Dark Theme
   ================================================================ */

/* --- Global defaults --------------------------------------------------- */
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_PRIMARY};
    font-size: 11pt;
}}

/* --- QMainWindow / QFrame containers ----------------------------------- */
QMainWindow {{
    background-color: {COLOR_BG};
}}

QFrame {{
    background-color: transparent;
}}

/* --- Card-style QFrame (use objectName or class for specificity) ------- */
QFrame[frameShape="StyledPanel"] {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 8px;
}}

QFrame#ChannelCard {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 8px;
}}

/* --- Labels ------------------------------------------------------------ */
QLabel {{
    background-color: transparent;
    border: none;
    color: {COLOR_TEXT_PRIMARY};
    font-size: 11pt;
}}

QLabel[role="secondary"] {{
    color: {COLOR_TEXT_SECONDARY};
}}

/* --- QPushButton ------------------------------------------------------- */
QPushButton {{
    background-color: {COLOR_BTN_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 11pt;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {COLOR_BTN_HOVER};
}}

QPushButton:pressed {{
    background-color: {COLOR_SURFACE_BORDER};
}}

QPushButton:disabled {{
    background-color: {COLOR_DISABLED_BG};
    color: {COLOR_DISABLED_TEXT};
    border: 1px solid {COLOR_SURFACE_BORDER};
}}

/* --- QComboBox --------------------------------------------------------- */
QComboBox {{
    background-color: {COLOR_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 24px;
    font-size: 11pt;
}}

QComboBox:hover {{
    border: 1px solid {COLOR_A};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLOR_TEXT_SECONDARY};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_SURFACE_BORDER};
    selection-background-color: {COLOR_BTN_HOVER};
    selection-color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

/* --- QRadioButton ------------------------------------------------------ */
QRadioButton {{
    background-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
    spacing: 6px;
    font-size: 11pt;
}}

QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 2px solid {COLOR_SURFACE_BORDER};
    border-radius: 9px;
    background-color: {COLOR_INPUT};
}}

QRadioButton::indicator:checked {{
    background-color: {COLOR_A};
    border: 2px solid {COLOR_A};
}}

/* --- QCheckBox --------------------------------------------------------- */
QCheckBox {{
    background-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
    spacing: 6px;
    font-size: 11pt;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLOR_SURFACE_BORDER};
    border-radius: 4px;
    background-color: {COLOR_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {COLOR_A};
    border: 2px solid {COLOR_A};
}}

/* --- QLineEdit / QSpinBox / QDoubleSpinBox ----------------------------- */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_INPUT};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11pt;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COLOR_A};
}}

/* --- QGroupBox --------------------------------------------------------- */
QGroupBox {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-size: 11pt;
    color: {COLOR_TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {COLOR_TEXT_SECONDARY};
}}

/* --- QMenuBar ---------------------------------------------------------- */
QMenuBar {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_PRIMARY};
    border-bottom: 1px solid {COLOR_SURFACE_BORDER};
    font-size: 11pt;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 4px 10px;
}}

QMenuBar::item:selected {{
    background-color: {COLOR_BTN_HOVER};
    border-radius: 4px;
}}

/* --- QMenu ------------------------------------------------------------- */
QMenu {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 6px;
    padding: 4px;
    font-size: 11pt;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLOR_BTN_HOVER};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLOR_SURFACE_BORDER};
    margin: 4px 8px;
}}

/* --- QStatusBar -------------------------------------------------------- */
QStatusBar {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_SECONDARY};
    border-top: 1px solid {COLOR_SURFACE_BORDER};
    font-size: 10pt;
}}

QStatusBar::item {{
    border: none;
}}

/* --- QTabWidget / QTabBar ---------------------------------------------- */
QTabWidget::pane {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: {COLOR_BTN_BG};
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 16px;
    margin-right: 2px;
    font-size: 11pt;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLOR_BTN_HOVER};
}}

/* --- QScrollBar (vertical) --------------------------------------------- */
QScrollBar:vertical {{
    background-color: {COLOR_BG};
    width: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {COLOR_SCROLLBAR};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_BTN_HOVER};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

/* --- QScrollBar (horizontal) ------------------------------------------- */
QScrollBar:horizontal {{
    background-color: {COLOR_BG};
    height: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLOR_SCROLLBAR};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLOR_BTN_HOVER};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    border: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* --- QToolTip ---------------------------------------------------------- */
QToolTip {{
    background-color: {COLOR_SURFACE};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_SURFACE_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10pt;
}}

/* --- QSplitter --------------------------------------------------------- */
QSplitter::handle {{
    background-color: {COLOR_SURFACE_BORDER};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* --- QDialog ----------------------------------------------------------- */
QDialog {{
    background-color: {COLOR_BG};
}}
"""

logger.debug("Dark theme QSS loaded (%d characters)", len(DARK_THEME))
