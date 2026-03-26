"""Numeric display panel for QCM-Dual application.

Contains ChannelCard (single-channel readout card) and DisplayPanel
(three side-by-side cards for channels A, B, and Diff).  Located in
Zone 2 of the main window.
"""
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.gui.styles import (
    COLOR_A,
    COLOR_B,
    COLOR_DIFF,
    COLOR_SURFACE,
    COLOR_SURFACE_BORDER,
    COLOR_TEXT_SECONDARY,
    MONO_FONT,
)

logger = logging.getLogger(__name__)

# Placeholder text shown before data is available
_PLACEHOLDER = "---"
_ZERO = "0.000"


class ChannelCard(QFrame):
    """Styled card showing numeric readouts for one channel.

    Channels A and B display: Frequency, delta-f, delta-m, ACG, Temperature.
    The Diff channel displays: delta-f(A-B), delta-m(A-B).

    The card has a colored left border accent strip whose color is set via
    the *accent_color* constructor argument.

    Args:
        channel: One of ``"A"``, ``"B"``, or ``"Diff"``.
        accent_color: CSS color string for the left accent border.
        parent: Optional parent widget.
    """

    def __init__(
        self,
        channel: str,
        accent_color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.channel = channel
        self._accent_color = accent_color
        self._value_labels: dict[str, QLabel] = {}
        self._row_labels: dict[str, QLabel] = {}
        self._title_label: QLabel | None = None
        self.setObjectName("ChannelCard")
        self._build_ui()
        logger.debug("ChannelCard '%s' initialized", channel)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the card layout with accent border and value rows."""
        # Apply card background + accent left border
        self.setStyleSheet(
            f"QFrame#ChannelCard {{"
            f"  background-color: {COLOR_SURFACE};"
            f"  border: 1px solid {COLOR_SURFACE_BORDER};"
            f"  border-left: 4px solid {self._accent_color};"
            f"  border-radius: 8px;"
            f"}}"
        )
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(2)

        # Channel title
        self._title_label = QLabel(self._title_text())
        self._title_label.setStyleSheet(
            f"color: {self._accent_color}; font-weight: bold; font-size: 12pt;"
            "background: transparent; border: none;"
        )
        outer.addWidget(self._title_label)

        # Value grid
        grid = QGridLayout()
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(2)

        if self.channel in ("A", "B"):
            rows = self._ab_rows()
        else:
            rows = self._diff_rows()

        for row_idx, (label_text, key, font_pt) in enumerate(rows):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                f"color: {COLOR_TEXT_SECONDARY}; font-size: 11pt;"
                "background: transparent; border: none;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            val = QLabel(_PLACEHOLDER if key in ("freq", "delta_f", "delta_m") else _ZERO)
            val.setStyleSheet(
                f"font-family: '{MONO_FONT}';"
                f"font-size: {font_pt}pt;"
                f"color: #e0e0e0;"
                "background: transparent; border: none;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val.setMinimumWidth(140)

            grid.addWidget(lbl, row_idx, 0)
            grid.addWidget(val, row_idx, 1)
            self._value_labels[key] = val
            self._row_labels[key] = lbl

        outer.addLayout(grid)
        outer.addStretch()

    def _title_text(self) -> str:
        """Return the card title string."""
        if self.channel == "Diff":
            return "Differential"
        return f"Channel {self.channel}"

    def set_diff_direction(self, ref_channel: str) -> None:
        """Update differential card labels to show the correct direction.

        Args:
            ref_channel: "A" (diff = B−A) or "B" (diff = A−B).
        """
        if self.channel != "Diff":
            return
        if ref_channel == "A":
            direction = "B\u2212A"
        else:
            direction = "A\u2212B"
        if "delta_f" in self._row_labels:
            self._row_labels["delta_f"].setText(f"\u0394f ({direction})")
        if "delta_m" in self._row_labels:
            self._row_labels["delta_m"].setText(f"\u0394m ({direction})")
        if self._title_label is not None:
            self._title_label.setText(f"Diff ({direction})")

    @staticmethod
    def _ab_rows() -> list[tuple[str, str, int]]:
        """Row definitions for channel A or B cards.

        Frequency shows raw Hz before tare, relative Hz after tare.

        Returns:
            List of (label_text, dict_key, font_point_size).
        """
        return [
            ("Frequency", "freq", 18),
            ("Temperature", "temp", 12),
        ]

    @staticmethod
    def _diff_rows() -> list[tuple[str, str, int]]:
        """Row definitions for the differential card.

        Δf = Sample − Reference (direction set by set_diff_direction).
        Δm = mass change via Sauerbrey from Δf.

        Returns:
            List of (label_text, dict_key, font_point_size).
        """
        return [
            ("\u0394f", "delta_f", 18),
            ("\u0394m", "delta_m", 14),
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_values(self, values: dict[str, str]) -> None:
        """Update displayed values from a dictionary.

        Keys should match the ``dict_key`` values defined in the row
        lists: ``freq``, ``delta_f``, ``delta_m``, ``acg``, ``temp``.
        Values are pre-formatted strings ready for display.

        Args:
            values: Mapping of key to formatted display string.
        """
        for key, text in values.items():
            label = self._value_labels.get(key)
            if label is not None:
                label.setText(text)
            else:
                logger.warning(
                    "ChannelCard '%s': unknown value key '%s'",
                    self.channel, key,
                )

    def reset(self) -> None:
        """Reset all value labels to placeholders."""
        for key, label in self._value_labels.items():
            label.setText(_PLACEHOLDER if key.startswith("delta") or key == "freq" else _ZERO)


class DisplayPanel(QFrame):
    """Container holding three ChannelCards side by side.

    Attributes:
        card_a: ChannelCard for channel A (blue accent).
        card_b: ChannelCard for channel B (red accent).
        card_diff: ChannelCard for differential (green accent).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        logger.debug("DisplayPanel initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create three channel cards in a horizontal layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        self.card_a = ChannelCard("A", COLOR_A, parent=self)
        self.card_b = ChannelCard("B", COLOR_B, parent=self)
        self.card_diff = ChannelCard("Diff", COLOR_DIFF, parent=self)

        layout.addWidget(self.card_a, stretch=1)
        layout.addWidget(self.card_b, stretch=1)
        layout.addWidget(self.card_diff, stretch=1)

        # Diff card hidden until a reference channel is selected
        self.card_diff.setVisible(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_display_mode(self, mode: str) -> None:
        """Switch between display modes.

        Args:
            mode: ``"all"`` shows all three cards, ``"diff"`` shows only
                  the differential card expanded to full width.
        """
        if mode == "diff":
            self.card_a.setVisible(False)
            self.card_b.setVisible(False)
            self.card_diff.setVisible(True)
        else:
            # Default: "all"
            self.card_a.setVisible(True)
            self.card_b.setVisible(True)
            # card_diff visibility depends on reference selection
        logger.debug("Display mode set to '%s'", mode)

    def set_reference_channel(self, ref: str) -> None:
        """Update display based on reference channel selection.

        Args:
            ref: "None", "Ch A", or "Ch B".
        """
        if ref == "None":
            self.card_diff.setVisible(False)
        elif ref == "Ch A":
            self.card_diff.set_diff_direction("A")
            self.card_diff.setVisible(True)
        elif ref == "Ch B":
            self.card_diff.set_diff_direction("B")
            self.card_diff.setVisible(True)
        logger.debug("Reference channel set to '%s'", ref)
