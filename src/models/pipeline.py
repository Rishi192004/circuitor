from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from src.models.validation import ValidationIssue
from src.models.suggestion import PatternSuggestion


@dataclass
class PipelineResult:
    """Structured API response envelope for the circuit validation pipeline."""
    status: str  # "success", "error", "warning"
    circuit_id: str
    phase_reached: str  # "TOPOLOGY", "PHYSICS", "SEMANTICS", or "ALL_PASSED"
    issues: List[ValidationIssue] = field(default_factory=list)
    suggestions: List[PatternSuggestion] = field(default_factory=list)
    graph: Optional[Dict[str, List[str]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def can_simulate(self) -> bool:
        """True when no ERROR-severity issues are present (warnings are acceptable)."""
        return not any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "circuit_id": self.circuit_id,
            "phase_reached": self.phase_reached,
            "can_simulate": self.can_simulate,
            "issues_count": len(self.issues),
            "issues": [issue.to_dict() for issue in self.issues],
            "suggestions_count": len(self.suggestions),
            "suggestions": [s.to_dict() for s in self.suggestions],
            "graph": self.graph,
            "metadata": self.metadata,
        }
