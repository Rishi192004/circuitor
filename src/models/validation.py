from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationIssue:
    rule_name: str
    message: str
    component_id: Optional[str] = None
    pin_name: Optional[str] = None
    severity: str = "error"  # "error" or "warning"
    
    def to_dict(self):
        return {
            "rule_name": self.rule_name,
            "message": self.message,
            "component_id": self.component_id,
            "pin_name": self.pin_name,
            "severity": self.severity
        }
