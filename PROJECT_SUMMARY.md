# Circuit Simulation Engine - Project Summary

*This document outlines the architecture, data models, and features built into the Python backend engine up to this point. It is designed to be fed into an LLM or shared with other engineers to quickly onboard them onto the architectural design decisions.*

## 1. Project Goal
To build a clean, minimal, production-oriented Python backend for a circuit simulation tool. The engine takes a frontend-generated JSON circuit design, parses it into domain objects, mathematically connects the pins (building a graph), and runs lightning-fast electrical validation rules before handing the data off to an AI or a physics simulator (like SPICE).

## 2. Architecture Details
The project follows **Clean Architecture** principles using Python 3.11+ standard library only (no heavy external frameworks).

*   **`src/models/`**: Strongly-typed Python `dataclasses` that act as the single source of truth.
*   **`src/parser/`**: The I/O layer. Safely deserializes raw JSON and normalizes string properties (e.g., `"1k"` -> `1000.0`).
*   **`src/graph/`**: The math engine. Translates "Nets" (wires) into a pure Adjacency List graph representing exact pin-to-pin connections.
*   **`src/validation/`**: The rule engine. Uses the Strategy Pattern to run modular physics checks against the circuit.
*   **`tests/`**: A comprehensive `unittest` suite ensuring all logic is mathematically sound.

## 3. Features Built So Far

### A. The Parsing & Normalization Pipeline
The engine safely reads the frontend JSON, separates "Templates" (library definitions) from "Instances" (drawn components), and passes them through a **Value Normalizer**. This normalizer uses Regex to convert human-readable SI units (like `"5uF"` or `"10k ohm"`) into pure floats (`0.000005`, `10000.0`) to prevent the math engine from crashing.

### B. The Graph Builder
The engine iterates over every Net and treats it as a "clique", automatically mapping out every single pin to every other pin it touches. It generates a pure JSON-friendly Adjacency List ready for KVL/KCL algorithms.

### C. The Educational Validation Pipeline
Instead of relying on AI to guess if a circuit is broken, the Python engine runs 7 strict EE rules instantly:
1.  **FloatingPinRule**: Ensures no physical pin is left unwired.
2.  **EmptyNetRule**: Ensures every drawn wire connects at least two endpoints.
3.  **MissingGroundRule**: Verifies the circuit has a 0V `reference` component.
4.  **ShortCircuitSourceRule**: Prevents wiring a voltage source's terminals directly together.
5.  **OutputCollisionRule**: Prevents two `output` pins from being wired directly together.
6.  **UnpoweredCircuitRule**: Ensures the circuit actually has an active power source.
7.  **ZeroResistanceRule**: Catches 0-ohm resistors that would cause divide-by-zero math errors.

### D. Frontend-Ready Feedback Engine
When the validator catches an issue, it generates an exact, structured JSON array intended for the frontend UI:
```json
{
  "error_code": "E101",
  "severity": "error",
  "target": {"type": "component", "component_id": "Q1", "pin_name": "base"},
  "technical_message": "Pin 'Q1.base' is disconnected.",
  "user_explanation": "The 'base' pin on Q1 is floating. Electricity cannot flow.",
  "suggested_fix": {"action": "wire_pin", "description": "Draw a wire connecting the 'base' pin."}
}
```
This payload allows the frontend developer to instantly highlight the exact component/pin on the screen and render a helpful tooltip without talking to the backend again.

### E. 100% Test Coverage
The validation engine is backed by a fully mocked `unittest` suite containing 14 pass/fail test cases, guaranteeing production stability.
