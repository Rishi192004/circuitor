import os
import sys
import logging

# Ensure src is in Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser.json_parser import CircuitParser
from src.graph.builder import GraphBuilder
from src.validation.validator import CircuitValidator
from src.validation.rules import FloatingPinRule

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

    # 2. Build Graph
    graph_builder = GraphBuilder(circuit)
    graph_builder.build()
    
    # 3. Print Connections
    print("\n--- Circuit Connections ---")
    graph_builder.print_connections()
    print("---------------------------\n")
    
    # 4. Validation (Optional Step)
    validator = CircuitValidator(circuit)
    validator.add_rule(FloatingPinRule())
    validator.validate()

if __name__ == "__main__":
    main()
