"""Tests for Sauerbrey equation."""
import logging

import pytest

from src.processing.sauerbrey import delta_f_to_delta_m

logger = logging.getLogger(__name__)


class TestSauerbrey:
    """Sauerbrey frequency-to-mass conversion."""

    def test_negative_delta_f_gives_positive_mass(self) -> None:
        """Mass adsorption (negative Δf) should give positive Δm."""
        result = delta_f_to_delta_m(-10.0, f0=10e6, area=0.2, harmonic=1)
        assert result > 0

    def test_positive_delta_f_gives_negative_mass(self) -> None:
        """Mass desorption (positive Δf) should give negative Δm."""
        result = delta_f_to_delta_m(10.0, f0=10e6, area=0.2, harmonic=1)
        assert result < 0

    def test_zero_delta_f_gives_zero_mass(self) -> None:
        assert delta_f_to_delta_m(0.0) == 0.0

    def test_known_value(self) -> None:
        """Δf = -10 Hz at 10 MHz, area=1.0 cm² → ~44.2 ng/cm² (published)."""
        result = delta_f_to_delta_m(-10.0, f0=10e6, area=1.0, harmonic=1)
        assert result == pytest.approx(44.2, rel=0.05)

    def test_higher_harmonic_reduces_sensitivity(self) -> None:
        """3rd harmonic should give smaller mass for same Δf."""
        m1 = delta_f_to_delta_m(-10.0, harmonic=1)
        m3 = delta_f_to_delta_m(-10.0, harmonic=3)
        assert m3 < m1

    def test_larger_area_gives_larger_mass(self) -> None:
        """Larger electrode area gives larger total mass change."""
        m_small = delta_f_to_delta_m(-10.0, area=0.1)
        m_large = delta_f_to_delta_m(-10.0, area=0.5)
        assert m_large > m_small
