"""Application entry point for QCM-Dual control software."""
import logging
import sys

from PySide6.QtWidgets import QApplication

from src.app_controller import AppController
from src.gui.main_window import MainWindow
from src.gui.styles import DARK_THEME

logger = logging.getLogger(__name__)


def main() -> None:
    """Launch the QCM-Dual application."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting QCM-Dual application")

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    controller = AppController(window)  # noqa: F841 — prevent GC
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
