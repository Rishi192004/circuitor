"""
base.py — Abstract base class (Strategy interface) for all circuit patterns.

Every pattern:
  - reads a Circuit and the list of ValidationIssues produced upstream
  - emits zero or more PatternSuggestions
  - NEVER modifies circuit state
  - NEVER decides whether a circuit is valid/invalid
"""

from abc import ABC, abstractmethod
from typing import List

from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.models.suggestion import PatternSuggestion


class Pattern(ABC):
    """
    Abstract base class for all pattern detectors.

    Subclasses implement ``match()`` to inspect the circuit and return
    suggestions. The Pattern Engine calls each registered pattern and
    aggregates results.
    """

    @property
    @abstractmethod
    def pattern_id(self) -> str:
        """
        Unique stable identifier for this pattern, e.g. ``"LED_MISSING_RESISTOR"``.
        Used for deduplication and frontend filtering.
        """

    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Execution and display priority. Lower number → higher priority.
        Range: 1 (critical actionable) … 100 (informational).
        """

    @abstractmethod
    def match(
        self,
        circuit: Circuit,
        validation_issues: List[ValidationIssue],
    ) -> List[PatternSuggestion]:
        """
        Analyse the circuit (and any validation context already gathered) and
        return a list of suggestions.

        Args:
            circuit:           The fully parsed and normalised circuit model.
            validation_issues: Issues already raised by the Validation Engine.
                               Patterns may use these to *skip* suggestions that
                               are already covered by validation errors, or to
                               provide complementary guidance.

        Returns:
            A (possibly empty) list of :class:`PatternSuggestion` objects.
            Must never raise; return ``[]`` on any unexpected condition.
        """
