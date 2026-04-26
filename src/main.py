import os
import sys
import logging
import json
from datetime import datetime, timezone

from src.parser.json_parser import CircuitParser
from src.parser.normalizer import ValueNormalizer
from src.graph.builder import GraphBuilder
from src.validation.validator import CircuitValidator
from src.validation.rules import (
    FloatingPinRule,
    EmptyNetRule,
    MissingGroundRule,
    ShortCircuitSourceRule,
    OutputCollisionRule,
    UnpoweredCircuitRule,
    ZeroResistanceRule,
    VoltageSourceLoopRule
)
from src.models.pipeline import PipelineResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# All available rules, registered in phase order
ALL_RULES = [
    FloatingPinRule(),
    EmptyNetRule(),
    MissingGroundRule(),
    ShortCircuitSourceRule(),
    OutputCollisionRule(),
    UnpoweredCircuitRule(),
    ZeroResistanceRule(),
    VoltageSourceLoopRule()
]


def run_pipeline(filepath: str) -> PipelineResult:
    """Runs the full circuit validation pipeline and returns a structured result.
    
    This is the primary API entrypoint. Flask/FastAPI/AI layers should call this function
    directly instead of invoking main().
    
    Args:
        filepath: Absolute or relative path to the circuit JSON file.
        
    Returns:
        PipelineResult with status, issues, graph, and metadata.
        
    Raises:
        FileNotFoundError: If the circuit file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    # 1. Parse JSON
    circuit = CircuitParser.parse_json(filepath)
    logger.info(f"Loaded circuit '{circuit.id}' with {len(circuit.components)} components and {len(circuit.nets)} nets.")

    # 2. Normalize Properties (e.g., "10k" -> 10000.0)
    ValueNormalizer.normalize_circuit(circuit)

    # 3. Build Graph & store on Circuit for downstream consumers
    graph_builder = GraphBuilder(circuit)
    circuit.graph = graph_builder.build()

    # 4. Run Phase-Based Validation
    validator = CircuitValidator(circuit)
    for rule in ALL_RULES:
        validator.add_rule(rule)
    
    issues, phase_reached = validator.validate()

    # 5. Determine overall status
    has_errors = any(i.severity == "error" for i in issues)
    has_warnings = any(i.severity == "warning" for i in issues)
    
    if has_errors:
        status = "error"
    elif has_warnings:
        status = "warning"
    else:
        status = "success"

    return PipelineResult(
        status=status,
        circuit_id=circuit.id,
        phase_reached=phase_reached,
        issues=issues,
        graph=circuit.graph,
        metadata={
            "components_count": len(circuit.components),
            "nets_count": len(circuit.nets),
            "rules_run": len(ALL_RULES),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


def main():
    """CLI wrapper — parses args and prints the pipeline result as JSON."""
    logger.info("Initializing Circuit Simulation Engine...")
    
    # Get file from arguments, default to sample_circuit.json
    filename = sys.argv[1] if len(sys.argv) > 1 else "sample_circuit.json"
    
    # Resolve path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_file = os.path.join(project_root, "data", filename)
    
    try:
        result = run_pipeline(target_file)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return
    
    # Pretty-print the full structured response
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
