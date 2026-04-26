# Circuit Simulation Engine - Project Summary

*This document outlines the architecture, data models, and features built into the Python backend engine up to this point. It is designed to be fed into an LLM or shared with other engineers to quickly onboard them onto the architectural design decisions.*

## 1. Project Goal
To build a clean, minimal, production-oriented Python backend for a circuit simulation tool. The engine takes a frontend-generated JSON circuit design, parses it into domain objects, mathematically connects the pins (building a graph), and runs lightning-fast electrical validation rules before handing the data off to an AI or a physics simulator (like SPICE).

## 2. Architecture Details
The project follows **Clean Architecture** principles using Python 3.11+ standard library only (no heavy external frameworks). All packages have proper `__init__.py` files for clean imports.

*   **`src/models/`**: Strongly-typed Python `dataclasses` that act as the single source of truth. Includes `PipelineResult` as the standardized API response envelope.
*   **`src/parser/`**: The I/O layer. Safely deserializes raw JSON and normalizes string properties (e.g., `"1k"` -> `1000.0`).
*   **`src/graph/`**: The math engine. Translates "Nets" (wires) into a pure Adjacency List graph. The graph is stored on the `Circuit` object for all downstream consumers.
*   **`src/validation/`**: The rule engine. Uses the Strategy Pattern with Phase-Based Orchestration (Topology -> Physics -> Semantics).
*   **`src/constants/`**: Shared enums (`ValidationPhase`).
*   **`tests/`**: A comprehensive `unittest` suite with 26 pass/fail test cases.

## 3. Features Built So Far

### A. The Parsing & Normalization Pipeline
The engine safely reads the frontend JSON, separates "Templates" (library definitions) from "Instances" (drawn components), and passes them through a **Value Normalizer**. This normalizer uses Regex to convert human-readable SI units (like `"5uF"` or `"10k ohm"`) into pure floats (`0.000005`, `10000.0`) to prevent the math engine from crashing.

### B. The Graph Engine & Cycle Detection
The engine iterates over every Net and treats it as a "clique", automatically mapping out every single pin to every other pin it touches to generate a pure JSON-friendly Adjacency List. The graph is stored directly on the `Circuit` object so validators, exporters, and AI layers can all consume it without rebuilding.
Additionally, `src/graph/algorithms.py` contains a custom **Depth-First Search (DFS) Cycle Detection** algorithm that projects the circuit into a Bipartite Graph to identify advanced parallel loops and global topology errors.

### C. The Phase-Based Validation Pipeline
Instead of relying on AI to guess if a circuit is broken, the Python engine runs 8 strict EE rules instantly. These rules are **Orchestrated into Phases** (Topology -> Physics -> Semantics). If a fatal error occurs in an early phase, the engine fast-fails to prevent cascading errors.
1.  **FloatingPinRule** (TOPOLOGY): Ensures no physical pin is left unwired.
2.  **EmptyNetRule** (TOPOLOGY): Ensures every drawn wire connects at least two endpoints.
3.  **MissingGroundRule** (PHYSICS): Verifies the circuit has a 0V `reference` component.
4.  **ShortCircuitSourceRule** (PHYSICS): Prevents wiring a voltage source's terminals directly together.
5.  **OutputCollisionRule** (PHYSICS): Prevents two `output` pins from being wired directly together.
6.  **UnpoweredCircuitRule** (PHYSICS): Ensures the circuit actually has an active power source.
7.  **VoltageSourceLoopRule** (PHYSICS): Uses the DFS Cycle Detection to catch fatal KVL violations.
8.  **ZeroResistanceRule** (SEMANTICS): Catches 0-ohm resistors that would cause divide-by-zero math errors.

### D. Frontend-Ready Feedback Engine
Every `suggested_fix` payload includes structured metadata for programmatic UI actions. Null values are automatically stripped from the JSON output for clean frontend consumption.
```json
{
  "error_code": "E101",
  "severity": "error",
  "target": {"type": "component", "component_id": "Q1", "pin_name": "base"},
  "technical_message": "Pin 'Q1.base' is disconnected.",
  "user_explanation": "The 'base' pin on Q1 is floating. Electricity cannot flow.",
  "suggested_fix": {
    "action": "wire_pin",
    "description": "Draw a wire connecting the 'base' pin.",
    "target_component_id": "Q1",
    "target_pin_name": "base"
  }
}
```

### E. Structured API Response Envelope
The engine wraps all output in a `PipelineResult` envelope, ready for direct consumption by Flask/FastAPI endpoints:
```json
{
  "status": "error",
  "circuit_id": "UI_FEEDBACK_DEMO",
  "phase_reached": "PHYSICS",
  "issues_count": 4,
  "issues": [...],
  "graph": {"V1.positive": ["R1.p1"], ...},
  "metadata": {"components_count": 2, "rules_run": 8, "timestamp": "..."}
}
```
The `run_pipeline(filepath)` function in `src/main.py` is the primary API entrypoint. Frontend/AI integrations should call this directly.

### F. Test Coverage
The engine is backed by **26 unit and integration tests** covering:
- Individual rule logic (pass/fail for all 8 rules)
- Graph cycle detection algorithms (2-source, 3-source loops)
- Graph builder correctness
- Phase orchestration (topology halt skips physics)
- API envelope structure and null-filtering
- Clean circuit "ALL_PASSED" path
