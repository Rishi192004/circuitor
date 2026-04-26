# Frontend Integration Guide — Circuitor Backend API

> **Audience:** Frontend engineer(s) building the circuit editor UI.
> **Author:** Backend team. **Last updated:** April 2026.
> **Version:** 1.0

---

## 1. How It Works (60-Second Overview)

```
┌──────────────┐       ┌──────────────────────────────────────────────┐       ┌──────────────┐
│  Frontend UI │──────▶│  Backend Pipeline (run_pipeline)             │──────▶│  JSON Report │
│  sends JSON  │       │  Parse → Normalize → Graph → Validate       │       │  PipelineResult │
└──────────────┘       └──────────────────────────────────────────────┘       └──────────────┘
```

1. The frontend serializes the user's schematic into a **Circuit JSON** (schema below).
2. The backend parses it, normalizes SI units, builds a graph, and runs validation rules.
3. The backend returns a **single `PipelineResult` JSON** containing the status, all issues, and the full graph.
4. The frontend reads the result and highlights errors/warnings on the canvas.

---

## 2. Input: Circuit JSON Schema

This is the JSON your frontend must produce. Every field marked 🔴 is **required**.

### Top-Level Object

| Field | Type | Required | Description |
|---|---|---|---|
| `circuit_id` | `string` | 🔴 | Unique ID for this circuit design. |
| `component_templates` | `array` | 🔴 | Library of available component types. |
| `components` | `array` | 🔴 | Instances the user placed on the canvas. |
| `nets` | `array` | 🔴 | Wires connecting pins together. |

### `component_templates[]` — The Component Library

Each entry defines a *type* of component (e.g., "Resistor", "DC Voltage Source").

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | 🔴 | Unique template ID (e.g., `"resistor"`, `"dc_voltage_source"`). |
| `name` | `string` | ⚪ | Display name (e.g., `"Resistor"`). |
| `category` | `string` | 🔴 | One of: `"passive"`, `"active"`, `"source"`, `"reference"`, `"ic"`. **This drives validation logic.** |
| `pins_template` | `array` | 🔴 | List of pin definitions. |
| `pins_template[].name` | `string` | 🔴 | Pin identifier (e.g., `"p1"`, `"positive"`, `"base"`). |
| `pins_template[].type` | `string` | 🔴 | One of: `"input"`, `"output"`, `"passive"`. **Drives output collision detection.** |
| `default_pins` | `number` | ⚪ | Number of pins (informational). |
| `property_schema` | `object` | ⚪ | Schema for editable properties. |

> [!IMPORTANT]
> **`category` is critical.** The backend uses it to decide which rules apply:
> - `"source"` → triggers short-circuit check, KVL loop detection
> - `"reference"` → satisfies the ground check
> - `"passive"` / `"active"` / `"ic"` → standard components

### `components[]` — User-Placed Instances

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | 🔴 | Unique instance ID (e.g., `"R1"`, `"V1"`). This is what the backend references in error targets. |
| `type` | `string` | 🔴 | Must match a `component_templates[].id`. |
| `circuit_id` | `string` | ⚪ | Defaults to top-level `circuit_id`. |
| `properties` | `object` | ⚪ | Values like `{"resistance": "10k"}`. Supports SI units — the backend normalizes automatically. |
| `metadata` | `object` | ⚪ | Frontend-only data (label, position, rotation). The backend ignores this. |

**SI Units you can send:** `"10k"`, `"5.5uF"`, `"2.2M ohm"`, `"100n"`, `"3.3p"` — all will be normalized to floats.

### `nets[]` — Wires

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | 🔴 | Unique wire ID (e.g., `"net_vcc"`). Referenced in error targets. |
| `wire_type` | `string` | ⚪ | Informational (e.g., `"power"`, `"signal"`). |
| `endpoints` | `array` | 🔴 | List of pin connections this wire touches. |
| `endpoints[].component_id` | `string` | 🔴 | Must match a `components[].id`. |
| `endpoints[].pin_name` | `string` | 🔴 | Must match a `pins_template[].name` on that component's template. |
| `properties` | `object` | ⚪ | Frontend-only data (color, thickness). |

### Minimal Valid Example

```json
{
  "circuit_id": "voltage_divider_1",
  "component_templates": [
    {
      "id": "resistor", "name": "Resistor", "category": "passive",
      "pins_template": [{"name": "p1", "type": "passive"}, {"name": "p2", "type": "passive"}],
      "default_pins": 2, "property_schema": {"resistance": {"type": "number", "unit": "ohm"}}
    },
    {
      "id": "dc_voltage_source", "name": "DC Voltage Source", "category": "source",
      "pins_template": [{"name": "positive", "type": "output"}, {"name": "negative", "type": "output"}],
      "default_pins": 2, "property_schema": {"voltage": {"type": "number", "unit": "volt"}}
    },
    {
      "id": "ground", "name": "Ground", "category": "reference",
      "pins_template": [{"name": "gnd", "type": "passive"}],
      "default_pins": 1, "property_schema": {}
    }
  ],
  "components": [
    {"id": "V1", "type": "dc_voltage_source", "properties": {"voltage": "12V"}},
    {"id": "R1", "type": "resistor", "properties": {"resistance": "1k"}},
    {"id": "R2", "type": "resistor", "properties": {"resistance": "2k"}},
    {"id": "G1", "type": "ground", "properties": {}}
  ],
  "nets": [
    {"id": "net_vcc", "endpoints": [{"component_id": "V1", "pin_name": "positive"}, {"component_id": "R1", "pin_name": "p1"}]},
    {"id": "net_mid", "endpoints": [{"component_id": "R1", "pin_name": "p2"}, {"component_id": "R2", "pin_name": "p1"}]},
    {"id": "net_gnd", "endpoints": [{"component_id": "R2", "pin_name": "p2"}, {"component_id": "V1", "pin_name": "negative"}, {"component_id": "G1", "pin_name": "gnd"}]}
  ]
}
```

---

## 3. Output: PipelineResult JSON Schema

This is the **single JSON object** the backend always returns.

### Top-Level Fields

| Field | Type | Always Present | Description |
|---|---|---|---|
| `status` | `string` | ✅ | `"success"`, `"warning"`, or `"error"`. |
| `circuit_id` | `string` | ✅ | Echoes the input circuit ID. |
| `phase_reached` | `string` | ✅ | Last validation phase completed. One of: `"TOPOLOGY"`, `"PHYSICS"`, `"SEMANTICS"`, `"ALL_PASSED"`. |
| `issues_count` | `number` | ✅ | Total number of issues found. |
| `issues` | `array` | ✅ | Array of issue objects (see below). Empty if `status === "success"`. |
| `graph` | `object` | ✅ | Adjacency list of pin-to-pin connections. |
| `metadata` | `object` | ✅ | `components_count`, `nets_count`, `rules_run`, `timestamp`. |

### Success Response (No Issues)

```json
{
  "status": "success",
  "circuit_id": "voltage_divider_1",
  "phase_reached": "ALL_PASSED",
  "issues_count": 0,
  "issues": [],
  "graph": {
    "V1.positive": ["R1.p1"],
    "R1.p1": ["V1.positive"],
    "R1.p2": ["R2.p1"],
    "R2.p1": ["R1.p2"],
    "R2.p2": ["V1.negative", "G1.gnd"],
    "V1.negative": ["R2.p2", "G1.gnd"],
    "G1.gnd": ["R2.p2", "V1.negative"]
  },
  "metadata": {
    "components_count": 4,
    "nets_count": 3,
    "rules_run": 8,
    "timestamp": "2026-04-26T15:50:37.036618+00:00"
  }
}
```

### Error Response (Issues Found)

```json
{
  "status": "error",
  "circuit_id": "UI_FEEDBACK_DEMO",
  "phase_reached": "PHYSICS",
  "issues_count": 4,
  "issues": [
    {
      "error_code": "E201",
      "rule_name": "Missing Ground Check",
      "severity": "error",
      "target": { "type": "global" },
      "technical_message": "Circuit lacks a 0V reference node.",
      "user_explanation": "Your circuit doesn't have a Ground!...",
      "suggested_fix": {
        "action": "add_ground",
        "description": "Add a 'Ground' component and connect it...",
        "suggested_component_type": "ground"
      }
    }
  ],
  "graph": { "..." : "..." },
  "metadata": { "..." : "..." }
}
```

---

## 4. Issue Object — Deep Dive

Each object in the `issues[]` array follows this structure. **Null fields are automatically stripped** — you will never receive a field with value `null`.

### Fields

| Field | Type | Description |
|---|---|---|
| `error_code` | `string` | Machine-readable code (e.g., `"E101"`). Use for programmatic switching. |
| `rule_name` | `string` | Human-readable rule name. Good for dev tools / logs. |
| `severity` | `string` | `"error"` (fatal, blocks simulation) or `"warning"` (informational). |
| `target` | `object` | **Where the problem is.** See target types below. |
| `technical_message` | `string` | Engineer-facing explanation. Show in dev console or advanced mode. |
| `user_explanation` | `string` | **Beginner-friendly.** Show this in tooltips and error panels. |
| `suggested_fix` | `object` | **Actionable metadata.** Drive your UI actions from this. See below. |

### Target Types

The `target.type` field tells you what kind of element to highlight:

| `target.type` | Fields Present | UI Action |
|---|---|---|
| `"component"` | `component_id`, `pin_name` | Highlight the specific pin on the component. |
| `"net"` | `net_id` | Highlight the wire (turn it red). |
| `"multiple"` | `component_ids` and/or `net_ids` | Highlight ALL listed elements (e.g., a battery loop). |
| `"global"` | *(none)* | Show a global banner / toast notification. |

**Example — targeting a specific pin:**
```json
"target": { "type": "component", "component_id": "R1", "pin_name": "p2" }
```

**Example — targeting multiple components in a loop:**
```json
"target": { "type": "multiple", "component_ids": ["V1", "V2"] }
```

### Suggested Fix Actions

The `suggested_fix.action` field tells your UI exactly what kind of fix to offer:

| `action` | Extra Fields | What Your UI Should Do |
|---|---|---|
| `"wire_pin"` | `target_component_id`, `target_pin_name` | Flash the unconnected pin. Show "Click to add wire" tooltip. |
| `"delete_or_connect"` | `target_net_id` | Highlight the dangling wire. Offer delete or connect buttons. |
| `"add_ground"` | `suggested_component_type: "ground"` | Show "Add Ground" button → auto-place a ground component. |
| `"add_source"` | `suggested_component_type: "voltage_source"` | Show "Add Power Source" button → open component library. |
| `"break_short"` | `target_component_id`, `target_net_id`, `suggested_component_type: "resistor"` | Highlight the shorted wire + source. Suggest inserting a resistor. |
| `"separate_outputs"` | `target_net_id` | Highlight the collision wire. |
| `"edit_property"` | `target_component_id`, `property_name` | Open the property editor panel for that component, focus the field. |
| `"break_loop"` | `target_component_ids`, `suggested_component_type: "resistor"` | Highlight all components in the loop. Suggest adding a resistor. |

---

## 5. Error Code Reference

### Topology Phase (E1xx) — "Is everything wired?"
| Code | Rule | Severity | Meaning |
|---|---|---|---|
| `E101` | FloatingPinRule | error | A pin has no wire connected to it. |
| `E102` | EmptyNetRule | warning | A wire has < 2 endpoints (dangling trace). |

### Physics Phase (E2xx–E3xx) — "Will the math work?"
| Code | Rule | Severity | Meaning |
|---|---|---|---|
| `E201` | MissingGroundRule | error | No ground/reference component found. |
| `E202` | UnpoweredCircuitRule | warning | No power source found. |
| `E301` | ShortCircuitSourceRule | error | A source's + and − are on the same wire. |
| `E302` | OutputCollisionRule | error | Two output pins wired directly together. |
| `E303` | ZeroResistanceRule | error | A resistor has 0Ω or invalid value. |
| `E304` | VoltageSourceLoopRule | error | Multiple sources form a closed loop (KVL violation). |

### Semantics Phase (E3xx) — "Is the design good?"
| Code | Rule | Severity | Meaning |
|---|---|---|---|
| `E303` | ZeroResistanceRule | error | (Also runs here) Zero-ohm resistor detected. |

> [!NOTE]
> **Phase blocking:** If any `severity: "error"` is found in TOPOLOGY, the engine **stops immediately** and will NOT run PHYSICS or SEMANTICS checks. This prevents cascading false positives. The `phase_reached` field tells you which phase the engine reached.

---

## 6. The Graph Object

The `graph` field in the response is an **adjacency list** mapping each pin to all pins it's electrically connected to.

```
graph["V1.positive"] → ["R1.p1"]     // V1's positive is wired to R1's p1
graph["R1.p1"]       → ["V1.positive"] // R1's p1 is wired to V1's positive
```

**Format:** `"<component_id>.<pin_name>": ["<component_id>.<pin_name>", ...]`

### Use Cases for Frontend:
- **Path tracing:** Animate current flow along connected pins.
- **Hover preview:** When hovering over a pin, highlight all connected pins.
- **Connectivity check:** Verify your wiring UI matches the backend's interpretation.

---

## 7. Frontend Integration Pseudocode

```javascript
// 1. Serialize the canvas state
const circuitJson = serializeCanvasToJSON(); // Your function

// 2. Send to backend
const response = await fetch("/api/validate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(circuitJson)
});
const result = await response.json();

// 3. Handle result
if (result.status === "success") {
  showSuccessBanner("Circuit is valid! Ready for simulation.");
  return;
}

// 4. Process issues
for (const issue of result.issues) {
  switch (issue.target.type) {
    case "component":
      highlightComponent(issue.target.component_id, issue.severity);
      highlightPin(issue.target.component_id, issue.target.pin_name);
      break;
    case "net":
      highlightWire(issue.target.net_id, issue.severity);
      break;
    case "multiple":
      for (const id of issue.target.component_ids || []) {
        highlightComponent(id, issue.severity);
      }
      break;
    case "global":
      showGlobalBanner(issue.user_explanation);
      break;
  }

  // 5. Render suggested fix button
  if (issue.suggested_fix.suggested_component_type) {
    showAddComponentButton(issue.suggested_fix.suggested_component_type);
  }
  if (issue.suggested_fix.target_component_id) {
    showFixTooltip(issue.suggested_fix.target_component_id, issue.suggested_fix.description);
  }
}
```

---

## 8. FAQ

**Q: Do I need to send `component_templates` every time?**
A: Yes. The backend is stateless — every request must include the full circuit including templates.

**Q: Can I send properties as strings like `"10k"`?**
A: Yes. The backend normalizes `"10k"` → `10000.0`, `"5uF"` → `0.000005`, etc. You can send raw user input.

**Q: What if the user hasn't placed any components yet?**
A: Send `"components": []` and `"nets": []`. You will receive a clean success response with zero issues.

**Q: Can I ignore `severity: "warning"` issues?**
A: Yes. Warnings are informational (e.g., "no power source"). Only `"error"` severity issues block simulation.

**Q: How do I know if the user fixed the issue and should re-validate?**
A: Re-send the entire circuit JSON. The backend is stateless — every call is a fresh validation.

**Q: What does `phase_reached: "TOPOLOGY"` mean?**
A: It means the engine found fatal errors in the wiring phase and stopped before checking physics. Once the user fixes the wiring, re-validate and the engine will proceed to PHYSICS.
