from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from src.models.validation import ValidationIssue


@dataclass
class PipelineResult:
    """Structured API response envelope for the circuit validation pipeline."""
    status: str  # "success", "error", "warning"
    circuit_id: str
    phase_reached: str  # "TOPOLOGY", "PHYSICS", "SEMANTICS", or "ALL_PASSED"
    issues: List[ValidationIssue] = field(default_factory=list)
    graph: Optional[Dict[str, List[str]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "circuit_id": self.circuit_id,
            "phase_reached": self.phase_reached,
            "issues_count": len(self.issues),
            "issues": [issue.to_dict() for issue in self.issues],
            "graph": self.graph,
            "metadata": self.metadata
        }
