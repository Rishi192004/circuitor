import logging
from src.models.circuit import Circuit
from src.validation.rules import ValidationRule

logger = logging.getLogger(__name__)

class CircuitValidator:
    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.rules = []
        
    def add_rule(self, rule: ValidationRule):
        self.rules.append(rule)
        
    def validate(self) -> bool:
        """Runs all validation rules against the circuit."""
        logger.info("Running circuit validation...")
        is_valid = True
        for rule in self.rules:
            if not rule.validate(self.circuit):
                logger.error(f"Validation failed for rule: {rule.name}")
                is_valid = False
        
        if is_valid:
            logger.info("Circuit validation passed.")
        return is_valid
