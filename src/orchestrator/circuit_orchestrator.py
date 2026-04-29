import logging
import os
from src.parser.json_parser import CircuitParser
from src.parser.normalizer import ValueNormalizer
from src.graph.builder import GraphBuilder
from src.validation.validator import CircuitValidator
from src.patterns import PatternEngine
from src.models.analysis_result import AnalysisResult, ValidationResult, PatternResult, GhostComponent

# Import registered rules and patterns from main pipeline
from src.main import ALL_RULES, ALL_PATTERNS

logger = logging.getLogger(__name__)

class CircuitOrchestrator:
    """
    Unified entry point for circuit analysis.
    Orchestrates parsing, normalization, graph building, validation, and pattern detection.
    """

    def analyze(self, circuit_path: str) -> AnalysisResult:
        """
        Runs the full analysis pipeline on a circuit file.
        
        Args:
            circuit_path: Path to the circuit JSON file.
            
        Returns:
            AnalysisResult in the unified format.
        """
        if not os.path.exists(circuit_path):
            raise FileNotFoundError(f"Circuit file not found: {circuit_path}")

        # 1. Parse JSON
        circuit = CircuitParser.parse_json(circuit_path)
        logger.info(f"Orchestrator: Analyzing circuit '{circuit.id}'")

        # 2. Normalize Properties (e.g., "10k" -> 10000.0)
        ValueNormalizer.normalize_circuit(circuit)

        # 3. Build Graph
        graph_builder = GraphBuilder(circuit)
        circuit.graph = graph_builder.build()

        # 4. Run Validation Engine
        validator = CircuitValidator(circuit)
        for rule in ALL_RULES:
            validator.add_rule(rule)
        
        issues, _ = validator.validate()

        # 5. Run Pattern Engine (always runs, even if validation has errors)
        pattern_engine = PatternEngine(ALL_PATTERNS)
        suggestions = pattern_engine.run(circuit, issues)

        # 6. Map to Unified Result Shape
        errors = []
        warnings = []
        for issue in issues:
            v_res = ValidationResult(
                error_code=issue.error_code,
                rule_name=issue.rule_name,
                severity=issue.severity,
                target=issue.to_dict()["target"],
                technical_message=issue.technical_message,
                user_explanation=issue.user_explanation,
                suggested_fix=issue.suggested_fix
            )
            if issue.severity == "error":
                errors.append(v_res)
            else:
                warnings.append(v_res)

        pattern_results = []
        ghost_components = []
        for s in suggestions:
            p_res = PatternResult(
                pattern_id=s.pattern_id,
                type=s.type,
                reason=s.reason,
                confidence=s.confidence,
                priority=s.priority,
                target_component_ids=s.target_component_ids,
                metadata=s.metadata
            )
            pattern_results.append(p_res)
            
            # Map specific suggestions to ghost components for the UI
            if s.type == "ADD_COMPONENT":
                ghost_components.append(GhostComponent(
                    type=s.component,
                    reason=s.reason,
                    metadata=s.metadata
                ))

        is_simulation_ready = len(errors) == 0

        return AnalysisResult(
            is_simulation_ready=is_simulation_ready,
            errors=errors,
            warnings=warnings,
            suggestions=pattern_results,
            ghost_components=ghost_components
        )
