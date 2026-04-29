"""
suggestion.py — Data model for a single Pattern Engine suggestion.

PatternSuggestions are completely separate from ValidationIssues.
They carry INTENT-based recommendations (what *could* improve the circuit),
never correctness verdicts (what IS wrong with it).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class PatternSuggestion:
    """
    Represents a single suggestion emitted by the Pattern Engine.

    Attributes:
        pattern_id:           Unique identifier for the pattern that fired,
                              e.g. ``"LED_MISSING_RESISTOR"``.
        type:                 Action category for the frontend/AI layer.
                              One of ``"ADD_COMPONENT"``, ``"ADD_CONNECTION"``,
                              ``"INSPECT_NODE"``.
        component:            Component type recommended (if applicable),
                              e.g. ``"resistor"``, ``"voltage_source"``.
        reason:               Human-readable explanation of why this is suggested.
        confidence:           0.0–1.0 score. 1.0 = heuristically certain;
                              lower values indicate weaker signals.
        priority:             Lower number → higher priority. Used to sort the
                              suggestion list before returning to the caller.
        target_component_ids: IDs of the components that triggered this pattern.
        metadata:             Open-ended extension bag for future AI / frontend use.
    """

    pattern_id: str
    type: str
    component: str
    reason: str
    confidence: float = 1.0
    priority: int = 50
    target_component_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    severity: str = "suggestion"  # "suggestion", "warning", or "error"

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-safe dictionary for the API response."""
        return {
            "pattern_id": self.pattern_id,
            "type": self.type,
            "component": self.component,
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "priority": self.priority,
            "severity": self.severity,
            "target_component_ids": self.target_component_ids,
            "metadata": self.metadata,
        }
