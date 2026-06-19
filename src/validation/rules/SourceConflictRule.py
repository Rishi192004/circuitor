from typing import List
from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.validation.rules import ValidationRule

class SourceConflictRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Source Conflict Check"

    def validate(self, circuit: Circuit) -> List[ValidationIssue]:
        """
        Detects multiple voltage sources connected to the same net with different voltage values.
        """
        issues = []
        for net_id, net in circuit.nets.items():
            source_voltages = {}
            for ep in net.endpoints:
                comp = circuit.components.get(ep.component_id)
                if comp and comp.type == "dc_voltage_source":
                    v_str = comp.properties.get("voltage", "0")
                    try:
                        v_val = float(str(v_str).lower().replace('v', ''))
                        source_voltages[comp.id] = v_val
                    except (ValueError, TypeError):
                        continue

            unique_voltages = set(source_voltages.values())
            if len(unique_voltages) > 1:
                conflict_desc = ", ".join([f"{cid}: {v}V" for cid, v in source_voltages.items()])
                issues.append(ValidationIssue(
                    error_code="E306",
                    rule_name=self.name,
                    technical_message=f"Net '{net_id}' has conflicting voltage sources: {conflict_desc}",
                    user_explanation=f"You have connected multiple voltage sources with different values ({conflict_desc}) to the same wire ('{net_id}'). This creates a heavy short circuit.",
                    suggested_fix={
                        "action": "remove_source",
                        "description": "Ensure all voltage sources connected to the same net have the same voltage, or remove the conflicting ones.",
                        "target_net_id": net_id
                    },
                    net_id=net_id,
                    component_ids=list(source_voltages.keys()),
                    severity="error"
                ))
        return issues
