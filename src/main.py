import os
import sys
import logging
import json

# Ensure src is in Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser.json_parser import CircuitParser
from src.parser.normalizer import ValueNormalizer
from src.graph.builder import GraphBuilder
from src.validation.validator import CircuitValidator
from src.validation.rules import (
    FloatingPinRule,
    EmptyNetRule,
    MissingGroundRule,
    ShortCircuitSourceRule,
    OutputCollisionRule
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Circuit Simulation Engine...")
    
    # Get file from arguments, default to sample_circuit.json
    filename = sys.argv[1] if len(sys.argv) > 1 else "sample_circuit.json"
    
    # Paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_file = os.path.join(project_root, "data", filename)
    
    # 1. Parse JSON
    try:
        circuit = CircuitParser.parse_json(target_file)
        logger.info(f"Loaded circuit with {len(circuit.components)} components and {len(circuit.nets)} nets.")
    except Exception as e:
        logger.error(f"Failed to load circuit: {e}")
        return

    # 1.5 Normalize Properties
    ValueNormalizer.normalize_circuit(circuit)

    # 2. Build Graph
    graph_builder = GraphBuilder(circuit)
    graph_builder.build()
    
    # 3. Print Connections
    print("\n--- Circuit Connections ---")
    graph_builder.print_connections()
    print("---------------------------\n")
    
    # 4. Validation
    validator = CircuitValidator(circuit)
    validator.add_rule(FloatingPinRule())
    validator.add_rule(EmptyNetRule())
    validator.add_rule(MissingGroundRule())
    validator.add_rule(ShortCircuitSourceRule())
    validator.add_rule(OutputCollisionRule())
    
    issues = validator.validate()
    
    print("\n--- Validation Report ---")
    if not issues:
        print("Success: No issues found! The circuit is ready for simulation.")
    else:
        print(f"Found {len(issues)} issue(s):\n")
        # Print out the issues as a JSON array for the frontend
        issues_dict_list = [issue.to_dict() for issue in issues]
        print(json.dumps(issues_dict_list, indent=2))
    print("-------------------------\n")

if __name__ == "__main__":
    main()
