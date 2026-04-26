# Circuit Simulation Engine & Frontend - Project Summary

*This document outlines the architecture, data models, and features built into the Circuitor project up to this point. It is designed to be fed into an LLM or shared with other engineers to quickly onboard them onto the architectural design decisions.*

## 1. Project Goal
To build a clean, minimal, production-oriented circuit simulation tool. The project consists of a high-fidelity, LTSpice-inspired React frontend (SVG canvas, drag-and-drop, wiring) and a Python backend engine that performs mathematical graph parsing and lightning-fast electrical validation before handing off to physics simulators (like SPICE) or AI.

## 2. Architecture Details

### Backend (Python 3.11+ Core Engine)
Follows **Clean Architecture** principles using standard library only for the core (no heavy external frameworks). Wrapped by a lightweight **FastAPI** layer for frontend communication.
*   **`src/models/`**: Strongly-typed Python `dataclasses` that act as the single source of truth. Includes `PipelineResult` as the standardized API response envelope.
*   **`src/parser/`**: The I/O layer. Safely deserializes raw JSON and normalizes string properties.
*   **`src/graph/`**: The math engine. Translates "Nets" (wires) into a pure Adjacency List graph.
*   **`src/validation/`**: The rule engine. Uses the Strategy Pattern with Phase-Based Orchestration.
*   **`api_server.py`**: A FastAPI application exposing the `/api/run_pipeline` endpoint to bridge the Python engine and the React frontend.

### Frontend (React 18 + Vite + Zustand)
A modern Single Page Application built for performance and complex state management.
*   **`src/store/circuitStore.js`**: A single Zustand store managing the absolute source of truth (`circuit_id`, `templates`, `instances`, `nets`). Automatically syncs to `localStorage` for session persistence.
*   **`src/components/canvas/`**: An SVG-based custom canvas (bypassing HTML5 Canvas API) for native React event handling, CSS styling, and sharp rendering. Implements snap-to-grid movement and orthogonal L-shaped wire routing.
*   **`src/serializer/`**: Translates the frontend's internal state into the exact `Circuit JSON` format required by the Python backend.

## 3. Features Built So Far

### A. Frontend: Canvas & Interactions
*   **Drag-and-Drop Sidebar**: A library of visually accurate, LTSpice-styled components (Resistors, Capacitors, Voltage Sources, Ground).
*   **Interactive Wiring**: Users click component pins to draw animated, dashed wires that route orthogonally across an LTSpice dot-grid.
*   **State Persistence**: The circuit state is serialized to `localStorage` on every mutation. On page reload, the canvas instantly rehydrates, intelligently syncing internal component ID counters to prevent collisions.

### B. The Backend: Parsing & Normalization
The engine safely reads the frontend JSON, separates "Templates" from "Instances", and passes them through a **Value Normalizer**. This normalizer uses Regex to convert human-readable SI units (like `"5uF"` or `"10k ohm"`) into pure floats (`0.000005`, `10000.0`) to prevent the math engine from crashing.

### C. The Backend: Graph Engine & Cycle Detection
The engine iterates over every Net and treats it as a "clique", automatically mapping out every single pin to every other pin it touches to generate a pure JSON-friendly Adjacency List. 
Additionally, `src/graph/algorithms.py` contains a custom **Depth-First Search (DFS) Cycle Detection** algorithm that projects the circuit into a Bipartite Graph to identify advanced parallel loops and global topology errors.

### D. Phase-Based Validation Pipeline
The Python engine runs 8 strict EE rules instantly. These rules are **Orchestrated into Phases** (Topology -> Physics -> Semantics). If a fatal error occurs in an early phase, the engine fast-fails.
1.  **FloatingPinRule** (TOPOLOGY): Ensures no physical pin is left unwired.
2.  **EmptyNetRule** (TOPOLOGY): Ensures every drawn wire connects at least two endpoints.
3.  **MissingGroundRule** (PHYSICS): Verifies the circuit has a 0V `reference` component.
4.  **ShortCircuitSourceRule** (PHYSICS): Prevents wiring a voltage source's terminals directly together.
5.  **OutputCollisionRule** (PHYSICS): Prevents two `output` pins from being wired directly together.
6.  **UnpoweredCircuitRule** (PHYSICS): Ensures the circuit actually has an active power source.
7.  **VoltageSourceLoopRule** (PHYSICS): Uses the DFS Cycle Detection to catch fatal KVL violations.
8.  **ZeroResistanceRule** (SEMANTICS): Catches 0-ohm resistors that would cause divide-by-zero math errors.

### E. Frontend-Ready Feedback Engine & UI
When the frontend POSTs a circuit, the backend responds with a structured `PipelineResult` envelope containing `suggested_fix` metadata.
*   The frontend **ValidationPanel** renders these issues as actionable cards with severity icons.
*   If validation stops early, a **Topology Banner** warns the user.
*   **Click-to-Highlight**: Clicking an issue card in the frontend UI automatically highlights the offending component or wire in red/amber on the SVG canvas.

### F. Test Coverage
The backend engine is backed by **26 unit and integration tests** covering pass/fail scenarios for all 8 rules, graph cycle detection algorithms, graph builder correctness, and API envelope structure.
