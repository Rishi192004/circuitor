# Circuit Simulation Engine - Project Summary

*This document outlines the architecture, data models, and features built into the Python backend engine up to this point. It is designed to be fed into an LLM or shared with other engineers to quickly onboard them onto the architectural design decisions.*

## 1. Project Goal
To build a clean, minimal, production-oriented Python backend for a circuit simulation tool. The engine takes a frontend-generated JSON circuit design, parses it into domain objects, mathematically connects the pins (building a graph), and runs lightning-fast electrical validation rules before handing the data off to an AI or a physics simulator (like SPICE).

## 2. Architecture Details
The project follows **Clean Architecture** principles using Python 3.11+ standard library only (no heavy external frameworks).

*   **`src/models/`**: Strongly-typed Python `dataclasses` that act as the single source of truth.
*   **`src/parser/`**: The I/O layer. Safely deserializes the raw frontend JSON into the internal domain models.
*   **`src/graph/`**: The math engine. Translates the "Nets" (wires) into a pure Adjacency List graph representing exact pin-to-pin connections.
*   **`src/validation/`**: The rule engine. Uses the Strategy Pattern to run modular physics checks against the circuit.

## 3. Data Schema Strategy
To prevent data duplication and allow for extensibility, the engine separates definitions from instances:
1.  **Component Templates**: Acts as the library/registry. Defines what a component is (e.g., `bjt_transistor`), what physical pins it has (`collector`, `base`, `emitter`), and its property schema.
2.  **Component Instances**: The actual components placed on the board (e.g., `Q1`). They inherit from a template but contain instance-specific `properties` and frontend `metadata` (like X/Y coordinates).
3.  **Nets**: The wires. Instead of components knowing what they connect to, Nets hold a list of `endpoints` (e.g., `[Q1.collector, Q2.base]`).

## 4. Features Built So Far

### A. The Graph Builder (`src/graph/builder.py`)
Instead of just printing a list of components, the engine iterates over every Net and treats it as a "clique". It automatically maps out every single pin to every other pin it touches, generating a pure JSON-friendly dictionary output (an Adjacency List) that looks like:
```json
{
    "V1.positive": ["R1.p1"],
    "R1.p1": ["V1.positive"]
}
```

### B. The Advanced Validation Pipeline (`src/validation/`)
Instead of sending raw JSON to an AI to ask "Is this circuit broken?" (which is slow, expensive, and prone to hallucinations), the Python engine runs pre-validation instantly. 

It implements 5 strict Electronics Engineering (EE) rules:
1.  **FloatingPinRule**: Checks template definitions to ensure no physical pin is left unwired.
2.  **EmptyNetRule**: Ensures every drawn wire connects at least two endpoints.
3.  **MissingGroundRule**: Verifies the circuit has a 0V `reference` component for physics math to work.
4.  **ShortCircuitSourceRule**: Prevents wiring a voltage source's positive and negative terminals directly together.
5.  **OutputCollisionRule**: Prevents two pins defined as `output` in their templates from being wired directly together.

### C. Frontend-Ready Error Reporting
When the validator catches an issue, it doesn't just log it to the backend console. It generates an exact, structured JSON array of `ValidationIssue` objects:
```json
[
  {
    "rule_name": "Floating Pin Check",
    "message": "Pin 'base' on component 'Q1' is floating.",
    "component_id": "Q1",
    "pin_name": "base",
    "severity": "error"
  }
]
```
This allows the frontend UI to instantly map the error back to the screen and draw a glowing red border around component `Q1`.

## 5. Next Steps
The foundation is complete. The next phases of this project involve:
1.  Writing a netlist generator that traverses the Adjacency List to output a `.net` file for a SPICE simulator.
2.  Integrating an AI module that analyzes the *validated* graph to provide circuit suggestions or auto-routing.
