from dataclasses import dataclass
from typing import Optional, Dict, List, Any

@dataclass
class ValidationIssue:
    error_code: str
    rule_name: str
    technical_message: str
    user_explanation: str
    suggested_fix: Dict[str, Any]
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
        
        # Build target dict, filtering out None values for clean frontend consumption
        target = {"type": target_type}
        if self.component_id is not None:
            target["component_id"] = self.component_id
        if self.component_ids is not None:
            target["component_ids"] = self.component_ids
        if self.pin_name is not None:
            target["pin_name"] = self.pin_name
        if self.net_id is not None:
            target["net_id"] = self.net_id
        if self.net_ids is not None:
            target["net_ids"] = self.net_ids
            
        return {
            "error_code": self.error_code,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "target": target,
            "technical_message": self.technical_message,
            "user_explanation": self.user_explanation,
            "suggested_fix": self.suggested_fix
        }

