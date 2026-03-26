"""Sauerbrey settings dialog for QCM-Dual application.

Allows the user to configure crystal parameters used in the Sauerbrey
equation for mass calculation: fundamental frequency, electrode area,
and harmonic number.
"""
import logging

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class SauerbreyDialog(QDialog):
    """Settings dialog for Sauerbrey crystal parameters.

    Provides spin-box inputs for fundamental frequency (f0), electrode
    area, and harmonic number. Values are read via properties after the
    dialog is accepted, or pre-populated via ``set_values()``.

    Attributes:
        f0_spin: QDoubleSpinBox for fundamental frequency (Hz).
        area_spin: QDoubleSpinBox for electrode area (cm^2).
        harmonic_spin: QSpinBox for harmonic number (odd integers).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sauerbrey Settings")
        self.setMinimumWidth(380)
        self._build_ui()
        logger.debug("SauerbreyDialog initialized")

    def _build_ui(self) -> None:
        """Build the dialog layout."""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Fundamental frequency f0
        self.f0_spin = QDoubleSpinBox()
        self.f0_spin.setRange(1e6, 20e6)
        self.f0_spin.setDecimals(0)
        self.f0_spin.setSuffix(" Hz")
        self.f0_spin.setValue(10_000_000.0)
        self.f0_spin.setSingleStep(100_000.0)
        self.f0_spin.setToolTip("Fundamental resonant frequency of the quartz crystal")
        form.addRow("Fundamental frequency f0:", self.f0_spin)

        # Electrode area
        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(0.01, 10.0)
        self.area_spin.setDecimals(2)
        self.area_spin.setSuffix(" cm\u00b2")
        self.area_spin.setValue(0.2)
        self.area_spin.setSingleStep(0.01)
        self.area_spin.setToolTip("Active electrode area of the QCM sensor")
        form.addRow("Electrode area:", self.area_spin)

        # Harmonic number
        self.harmonic_spin = QSpinBox()
        self.harmonic_spin.setRange(1, 9)
        self.harmonic_spin.setSingleStep(2)
        self.harmonic_spin.setValue(1)
        self.harmonic_spin.setToolTip("Overtone harmonic number (odd integers: 1, 3, 5, 7, 9)")
        form.addRow("Harmonic number:", self.harmonic_spin)

        layout.addLayout(form)

        # OK / Cancel
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def f0(self) -> float:
        """Fundamental frequency in Hz."""
        return self.f0_spin.value()

    @property
    def area(self) -> float:
        """Electrode area in cm^2."""
        return self.area_spin.value()

    @property
    def harmonic(self) -> int:
        """Harmonic number (odd integer)."""
        return self.harmonic_spin.value()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_values(self, f0: float, area: float, harmonic: int) -> None:
        """Populate the spin boxes with existing values.

        Args:
            f0: Fundamental frequency in Hz.
            area: Electrode area in cm^2.
            harmonic: Harmonic number (1, 3, 5, 7, or 9).
        """
        self.f0_spin.setValue(f0)
        self.area_spin.setValue(area)
        self.harmonic_spin.setValue(harmonic)
        logger.debug(
            "Sauerbrey values set: f0=%.0f Hz, area=%.2f cm², harmonic=%d",
            f0, area, harmonic,
        )
