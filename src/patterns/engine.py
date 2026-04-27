"""
engine.py — PatternEngine: orchestrates all registered patterns.

The PatternEngine is the single entry-point for the suggestion layer.
It:
  - Accepts a list of Pattern instances.
  - Calls each pattern's match() in priority order.
  - Aggregates and returns the sorted suggestion list.
  - Never influences validation status or simulation readiness.
"""

import logging
from typing import List

from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.models.suggestion import PatternSuggestion
from src.patterns.base import Pattern

logger = logging.getLogger(__name__)


class PatternEngine:
    """
    Orchestrates circuit pattern detection.

    Usage::

        engine = PatternEngine([LEDPattern(), OpAmpPattern()])
        suggestions = engine.run(circuit, validation_issues)
    """

    def __init__(self, patterns: List[Pattern]) -> None:
        """
        Args:
            patterns: Ordered list of Pattern instances.  The engine sorts them
                      by ``priority`` before execution, so the caller's order
                      doesn't matter.
        """
        self._patterns: List[Pattern] = sorted(patterns, key=lambda p: p.priority)
        logger.debug(
            "PatternEngine initialised with %d pattern(s): %s",
            len(self._patterns),
            [p.pattern_id for p in self._patterns],
        )

    def run(
        self,
        circuit: Circuit,
        validation_issues: List[ValidationIssue],
    ) -> List[PatternSuggestion]:
        """
        Run all registered patterns and return a deduplicated, priority-sorted
        suggestion list.

        The engine is intentionally defensive: a single pattern raising an
        exception must not crash the entire pipeline — it logs the error and
        continues.

        Args:
            circuit:           Normalised circuit model with graph populated.
            validation_issues: Issues from the Validation Engine (read-only).

        Returns:
            List of :class:`PatternSuggestion` sorted by (priority, pattern_id).
        """
        all_suggestions: List[PatternSuggestion] = []

        for pattern in self._patterns:
            try:
                results = pattern.match(circuit, validation_issues)
                if results:
                    logger.info(
                        "Pattern '%s' fired %d suggestion(s).",
                        pattern.pattern_id,
                        len(results),
                    )
                all_suggestions.extend(results)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Pattern '%s' raised an unexpected error and will be skipped: %s",
                    pattern.pattern_id,
                    exc,
                    exc_info=True,
                )

        # Sort final list by (priority, pattern_id) for deterministic output
        all_suggestions.sort(key=lambda s: (s.priority, s.pattern_id))

        logger.info(
            "PatternEngine produced %d total suggestion(s).", len(all_suggestions)
        )
        return all_suggestions
