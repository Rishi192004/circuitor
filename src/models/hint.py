"""
hint.py — Data model for Simulation Hints.

SimulationHints are informational notes that describe trivial or 
misleading simulation results in electrically valid circuits.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SimulationHint:
    """
    Represents a single hint emitted by the Hint Engine.

    Attributes:
        hint_id:              Unique identifier for the hint, e.g. "NO_LOAD_SOURCE".
        message:              Human-readable explanation.
        target_component_ids: IDs of the components that triggered this hint.
        metadata:             Additional context for UI or analysis.
    """
    hint_id: str
    message: str
    target_component_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hint_id": self.hint_id,
            "message": self.message,
            "target_component_ids": self.target_component_ids,
            "metadata": self.metadata,
        }
