import logging
from typing import List
from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.validation.rules import ValidationRule

logger = logging.getLogger(__name__)

class CircuitValidator:
    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.rules: List[ValidationRule] = []
        
    def add_rule(self, rule: ValidationRule):
        self.rules.append(rule)
        
    def validate(self) -> List[ValidationIssue]:
        """Runs all validation rules against the circuit and returns any issues found."""
        logger.info("Running circuit validation...")
        all_issues = []
        for rule in self.rules:
            issues = rule.validate(self.circuit)
            if issues:
                logger.warning(f"Rule '{rule.name}' found {len(issues)} issues.")
                all_issues.extend(issues)
        
        if not all_issues:
            logger.info("Circuit validation passed. No issues found.")
        return all_issues
