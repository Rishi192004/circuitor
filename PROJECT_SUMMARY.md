# Circuitor - Production Project Summary

## Executive Summary
Circuitor is a production-grade circuit design and validation platform that combines a visual schematic editor with a deterministic electrical rule engine and an intent-based pattern suggestion engine. Users draw circuits on an interactive SVG canvas, submit designs to a Python backend, and receive structured, layered feedback: strict correctness issues from the Validation Engine and improvement suggestions from the Pattern Engine.

Circuitor shortens design iteration loops by detecting topology and electrical issues early, before expensive downstream simulation or hardware workflows, while also guiding users toward best-practice circuit patterns.

## Problem and Market Need
Circuit teams often lose time between drafting a schematic and validating basic correctness. Lightweight editors are easy to use but weak on rule validation, while advanced EDA tooling can be heavy for rapid early-stage checks.

Circuitor addresses this gap with immediate, design-time intelligence: draw, validate, fix, and revalidate in seconds — with actionable guidance at every step.

## What Circuitor Does Today
- Provides a modern frontend editor for component placement and wiring.
- Serializes circuit state into backend-compatible JSON.
- Parses and normalizes electrical values (for example `1k -> 1000.0`).
- Builds connectivity graphs from net/pin relationships.
- Runs phase-based validation rules with controlled execution and fatal gating.
- Runs a separate Pattern Engine that detects intent-based improvement opportunities.
- Returns `PipelineResult` with status, issues, suggestions, `can_simulate`, graph data, and metadata.
- Renders issue cards and canvas highlights with suggestion-driven fixes.
- Renders ghost components on the canvas for keyboard-driven suggestion acceptance.

## End-to-End Product Flow
1. User creates or edits a schematic in the frontend canvas.
2. Zustand store captures instances, nets, templates, and validation state.
3. Serializer converts frontend net strings into backend pin objects.
4. Frontend POSTs payload to `/api/run_pipeline`.
5. Backend pipeline executes: Parser -> Normalizer -> Graph -> Validation Engine -> Pattern Engine.
6. Backend returns structured `PipelineResult` with issues and suggestions as separate arrays.
7. Frontend displays issue cards, phase banners, and component/net highlights.
8. Pattern suggestions render ghost components; Tab-to-focus / Enter-to-accept workflow places them.

## Technical Architecture

### Backend (Python 3.11+, Clean Architecture)
- `src/models`: dataclasses for circuit entities, `PipelineResult`, and `PatternSuggestion`
- `src/parser`: JSON ingest + SI normalization
- `src/graph`: adjacency list generation + DFS cycle logic
- `src/validation`: phase-based rule engine (Strategy pattern) — correctness only
- `src/patterns`: Pattern Engine with Strategy-pattern detectors — suggestions only
- `api_server.py`: FastAPI wrapper and health endpoint

### Backend Layer Separation (Key Architectural Principle)
The backend enforces a strict boundary between two layers:

| Layer | Responsibility | Output |
|---|---|---|
| **Validation Engine** | Detect errors and warnings. Determine simulation readiness. | `issues[]` |
| **Pattern Engine** | Detect topology patterns. Suggest improvements. | `suggestions[]` |

The Pattern Engine **never** sets status, blocks simulation, or marks a circuit valid/invalid.

### Frontend (React 18, Vite, Zustand)
- SVG schematic canvas (20px grid, orthogonal routing, dark LTSpice-inspired UI)
- Central store (`circuitStore.js`) as single source of truth
- Serializer boundary (`toBackendFormat.js`) for API contract compliance
- Validation UX (`ValidationPanel`) with issue cards and topology banner
- Ghost suggestion layer (`parseSuggestions.js`) with Tab-to-focus / Tab-to-accept

## Validation Engine Coverage
Validation runs in ordered phases with fail-fast logic:

- **Topology (fatal gate)**:
  - `FloatingPinRule` — detects unconnected component pins
  - `EmptyNetRule` — detects wires with fewer than two endpoints
- **Physics**:
  - `MissingGroundRule` — detects absence of a 0V reference node
  - `ShortCircuitSourceRule` — detects source pins shorted on a single net
  - `OutputCollisionRule` — detects multiple output pins shorted together
  - `UnpoweredCircuitRule` — detects circuits with no active power source
  - `VoltageSourceLoopRule` — detects KVL-violating source loops (DFS)
- **Semantics**:
  - `ZeroResistanceRule` — detects resistors with zero or invalid resistance

## Pattern Engine Coverage
Patterns run after validation and are always non-blocking:

- **`LEDPattern`** (`priority=10`, `confidence=0.95`):
  Detects LEDs driven directly from a voltage source without a current-limiting series resistor. Suggests `ADD_COMPONENT(resistor)`. Uses two-tier pin classification to avoid false positives on return/GND nets.

- **`OpAmpPattern`** (`priority=20`, `confidence=0.90/0.75`):
  Two sub-checks:
  - Missing power rails (VCC/VDD or VEE/GND unconnected) → `ADD_COMPONENT(voltage_source/ground)`
  - Missing feedback loop (output not routed back to inverting input) → `ADD_CONNECTION(resistor)`

- **`VoltageDividerPattern`** (`priority=30`, `confidence=0.80`):
  Detects two resistors forming a series voltage divider across a source where the midpoint node is unused. Suggests `INSPECT_NODE` to exploit the voltage tap.

Each pattern emits `PatternSuggestion` objects with `pattern_id`, `type`, `component`, `reason`, `confidence`, `priority`, `target_component_ids`, and `metadata`.

## API Contract (Current)
- Endpoint: `POST /api/run_pipeline`
- Input: `circuit_id`, `component_templates`, `components`, `nets`
- Output: `PipelineResult` including:
  - `status` (`success`, `warning`, `error`)
  - `phase_reached`
  - `can_simulate` — `true` when no error-severity issues exist
  - `issues_count`, `issues[]` — from Validation Engine; each includes `suggested_fix` for frontend Ghost Node compatibility
  - `suggestions_count`, `suggestions[]` — from Pattern Engine; structured intent-based recommendations
  - `graph`
  - `metadata` (`components_count`, `nets_count`, `rules_run`, `patterns_run`, `timestamp`)

## Product Readiness and Reliability
- End-to-end frontend-to-backend validation loop is implemented.
- FastAPI integration is production-ready for web clients.
- Auto-validation is integrated with debounced mutation tracking.
- Network failure states are handled in the UI.
- Backend quality is covered by **94 unit/integration tests** with 0 failures.
- Pattern Engine is fault-tolerant: a pattern exception is logged and skipped, never crashes the pipeline.
- API response is fully backward compatible — no fields were removed.

## Differentiators
- Real-time actionable validation during circuit creation, not only after export.
- Clean architectural separation: Validation Engine (correctness) vs Pattern Engine (suggestions).
- Structured issue targeting for precise UI highlighting and guided correction.
- Deterministic, modular backend suitable for scaling both rule packs and pattern packs.
- Keyboard-driven ghost suggestion workflow that accelerates iteration speed.
- AI-ready architecture: the Pattern Engine output layer is designed as the insertion point for an AI suggestion layer.

## Commercial Value
- Reduces engineering rework by catching errors earlier.
- Improves design velocity through fast feedback cycles at two levels (correctness + best practice).
- Lowers onboarding friction with guided visual correction and component suggestions.
- Creates a strong platform foundation for simulation integrations, AI assistance, and team collaboration features.

## Run Commands
- Backend CLI: `python src/main.py`
- Tests: `python -m unittest discover tests`
- Pattern tests only: `python -m unittest discover tests/patterns`
- Integration tests only: `python -m unittest discover tests/integration`
- API Server: `uvicorn api_server:app --reload --port 8000`
