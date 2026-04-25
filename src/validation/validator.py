import logging
from typing import List, Dict
from src.models.circuit import Circuit
from src.models.validation import ValidationIssue
from src.validation.rules import ValidationRule
from src.constants.enums import ValidationPhase

logger = logging.getLogger(__name__)

class CircuitValidator:
    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.rules: List[ValidationRule] = []
        
    def add_rule(self, rule: ValidationRule):
        self.rules.append(rule)
        
    def validate(self) -> List[ValidationIssue]:
        """Runs validation rules sequentially by phase. Halts if fatal errors occur in a phase."""
        logger.info("Running phase-based circuit validation...")
        all_issues = []
        
        # Group rules by phase
        phases_map: Dict[ValidationPhase, List[ValidationRule]] = {
            ValidationPhase.TOPOLOGY: [],
            ValidationPhase.PHYSICS: [],
            ValidationPhase.SEMANTICS: []
        }
        
        for rule in self.rules:
            phases_map[rule.phase].append(rule)
            
        # Execute phases in order
        for phase in [ValidationPhase.TOPOLOGY, ValidationPhase.PHYSICS, ValidationPhase.SEMANTICS]:
            phase_issues = []
            for rule in phases_map[phase]:
                issues = rule.validate(self.circuit)
                if issues:
                    logger.warning(f"Rule '{rule.name}' found {len(issues)} issues in phase {phase.name}.")
                    phase_issues.extend(issues)
                    
            all_issues.extend(phase_issues)
            
            # Fast-Fail: If any ERROR level issues found in this phase, halt validation
            if any(issue.severity == "error" for issue in phase_issues):
                logger.error(f"Fatal errors detected in phase {phase.name}. Halting validation.")
                break
                
        if not all_issues:
            logger.info("Circuit validation passed perfectly across all phases.")
        return all_issues
