from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ValidationResult:
    error_code: str
    rule_name: str
    severity: str
    target: Dict[str, Any]
    technical_message: str
    user_explanation: str
    suggested_fix: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "errorCode": self.error_code,
            "ruleName": self.rule_name,
            "severity": self.severity,
            "target": self.target,
            "technicalMessage": self.technical_message,
            "userExplanation": self.user_explanation,
            "suggestedFix": self.suggested_fix
        }

@dataclass
class PatternResult:
    pattern_id: str
    type: str
    reason: str
    confidence: float
    priority: int
    target_component_ids: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patternId": self.pattern_id,
            "type": self.type,
            "reason": self.reason,
            "confidence": self.confidence,
            "priority": self.priority,
            "targetComponentIds": self.target_component_ids,
            "metadata": self.metadata
        }

@dataclass
class GhostComponent:
    type: str
    reason: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "reason": self.reason,
            "metadata": self.metadata
        }

@dataclass
class HintResult:
    hint_id: str
    message: str
    target_component_ids: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hintId": self.hint_id,
            "message": self.message,
            "targetComponentIds": self.target_component_ids,
            "metadata": self.metadata
        }

@dataclass
class AnalysisResult:
    is_simulation_ready: bool
    errors: List[ValidationResult] = field(default_factory=list)
    warnings: List[ValidationResult] = field(default_factory=list)
    suggestions: List[PatternResult] = field(default_factory=list)
    ghost_components: List[GhostComponent] = field(default_factory=list)
    hints: List[HintResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "isSimulationReady": self.is_simulation_ready,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "suggestions": [s.to_dict() for s in self.suggestions],
            "ghostComponents": [g.to_dict() for g in self.ghost_components],
            "hints": [h.to_dict() for h in self.hints]
        }
