from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class ValidationIssue:
    error_code: str
    rule_name: str
    technical_message: str
    user_explanation: str
    suggested_fix: Dict[str, str]
    component_id: Optional[str] = None
    pin_name: Optional[str] = None
    net_id: Optional[str] = None
    component_ids: Optional[List[str]] = None
    net_ids: Optional[List[str]] = None
    severity: str = "error"  # "error" or "warning"
    
    def to_dict(self):
        target_type = "global"
        if self.component_ids or self.net_ids:
            target_type = "multiple"
        elif self.net_id:
            target_type = "net"
        elif self.component_id:
            target_type = "component"
            
        return {
            "error_code": self.error_code,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "target": {
                "type": target_type,
                "component_id": self.component_id,
                "component_ids": self.component_ids,
                "pin_name": self.pin_name,
                "net_id": self.net_id,
                "net_ids": self.net_ids
            },
            "technical_message": self.technical_message,
            "user_explanation": self.user_explanation,
            "suggested_fix": self.suggested_fix
        }
