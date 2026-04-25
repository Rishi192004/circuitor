from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class ValidationIssue:
    error_code: str
    rule_name: str
    technical_message: str
    user_explanation: str
    suggested_fix: Dict[str, str]
    component_id: Optional[str] = None
    pin_name: Optional[str] = None
    severity: str = "error"  # "error" or "warning"
    
    def to_dict(self):
        return {
            "error_code": self.error_code,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "target": {
                "type": "component" if self.component_id else "global",
                "component_id": self.component_id,
                "pin_name": self.pin_name
            },
            "technical_message": self.technical_message,
            "user_explanation": self.user_explanation,
            "suggested_fix": self.suggested_fix
        }
