"""Sauerbrey equation for QCM mass calculation.

Converts frequency change (Δf) to mass change (Δm) using the
Sauerbrey equation for rigid thin films on quartz crystal resonators.
"""
import logging
import math

logger = logging.getLogger(__name__)

# Quartz crystal constants
MU_Q = 2.947e11    # Shear modulus (g·cm⁻¹·s⁻²)
RHO_Q = 2.648      # Density (g/cm³)


def delta_f_to_delta_m(
    delta_f: float,
    f0: float = 10e6,
    area: float = 0.2,
    harmonic: int = 1,
) -> float:
    """Convert frequency change to mass change using Sauerbrey equation.

    Δm = -(Δf × A × √(μq × ρq)) / (2 × n × f0²)

    Args:
        delta_f: Frequency change in Hz (negative = mass added).
        f0: Fundamental resonant frequency in Hz.
        area: Active electrode area in cm².
        harmonic: Harmonic number (1, 3, 5...).

    Returns:
        Mass change in ng/cm².
    """
    sensitivity = 2 * harmonic * f0**2 / (area * math.sqrt(MU_Q * RHO_Q))
    delta_m_g_per_cm2 = -delta_f / sensitivity
    return delta_m_g_per_cm2 * 1e9  # g/cm² → ng/cm²
