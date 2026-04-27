"""
tests/integration/test_full_pipeline.py
Integration tests: JSON → Parser → Normalizer → Graph → Validation → PatternEngine → PipelineResult

These tests drive the actual src/main.py run_pipeline() using the fixture JSON files
in data/, so they exercise the entire stack end-to-end.

Test categories:
  (A) Valid circuit      → status=success, 0 issues, 0 suggestions, can_simulate=True
  (B) LED circuit        → validation clean, LED_MISSING_RESISTOR suggestion present
  (C) Op-amp circuit     → validation may have warnings; OPAMP_MISSING_POWER suggestions
  (D) API shape          → all expected top-level keys present in to_dict()
  (E) Edge cases         → empty circuit file, overlapping patterns
  (F) Regression         → existing ValidationIssue.suggested_fix still present
  (G) PatternEngine isolation → suggestions never affect status or can_simulate for valid circuits
"""

import json
import os
import tempfile
import unittest

from src.main import run_pipeline
from src.models.pipeline import PipelineResult

# Path to the data/ directory relative to this file's location
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
)


def _fixture(name: str) -> str:
    """Return the absolute path to a JSON fixture file."""
    return os.path.join(DATA_DIR, name)


def _write_circuit(data: dict) -> str:
    """Write a dict as a temp JSON file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    return path


# ── Shared minimal circuit builder ────────────────────────────────────────────

def _minimal_circuit(circuit_id="test", extra_comps=None, extra_nets=None):
    """Return a JSON-serialisable dict for a V1→R1→GND circuit."""
    base = {
        "circuit_id": circuit_id,
        "component_templates": [
            {
                "id": "dc_voltage_source", "name": "DC Voltage Source",
                "category": "source",
                "pins_template": [{"name": "positive", "type": "output"}, {"name": "negative", "type": "output"}],
                "default_pins": 2, "property_schema": {},
            },
            {
                "id": "resistor", "name": "Resistor", "category": "passive",
                "pins_template": [{"name": "p1", "type": "passive"}, {"name": "p2", "type": "passive"}],
                "default_pins": 2, "property_schema": {},
            },
            {
                "id": "ground", "name": "Ground", "category": "reference",
                "pins_template": [{"name": "gnd", "type": "passive"}],
                "default_pins": 1, "property_schema": {},
            },
        ],
        "components": [
            {"id": "V1", "type": "dc_voltage_source", "circuit_id": circuit_id, "properties": {"voltage": "5"}, "metadata": {}},
            {"id": "R1", "type": "resistor",           "circuit_id": circuit_id, "properties": {"resistance": "1k"}, "metadata": {}},
            {"id": "G1", "type": "ground",             "circuit_id": circuit_id, "properties": {}, "metadata": {}},
        ],
        "nets": [
            {"id": "n1", "circuit_id": circuit_id, "wire_type": "signal",
             "endpoints": [{"component_id": "V1", "pin_name": "positive"}, {"component_id": "R1", "pin_name": "p1"}],
             "properties": {}},
            {"id": "n2", "circuit_id": circuit_id, "wire_type": "signal",
             "endpoints": [{"component_id": "R1", "pin_name": "p2"}, {"component_id": "V1", "pin_name": "negative"}, {"component_id": "G1", "pin_name": "gnd"}],
             "properties": {}},
        ],
    }
    if extra_comps:
        base["components"].extend(extra_comps)
    if extra_nets:
        base["nets"].extend(extra_nets)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# (A) Valid circuit
# ══════════════════════════════════════════════════════════════════════════════

class TestValidCircuitPipeline(unittest.TestCase):
    """Full pipeline on data/valid_circuit.json — expects 0 issues, 0 suggestions."""

    def setUp(self):
        self.result = run_pipeline(_fixture("valid_circuit.json"))

    def test_status_is_success(self):
        self.assertEqual(self.result.status, "success")

    def test_zero_issues(self):
        self.assertEqual(len(self.result.issues), 0)

    def test_zero_suggestions(self):
        self.assertEqual(len(self.result.suggestions), 0)

    def test_can_simulate_true(self):
        self.assertTrue(self.result.can_simulate)

    def test_graph_is_populated(self):
        self.assertIsNotNone(self.result.graph)
        self.assertGreater(len(self.result.graph), 0)

    def test_phase_reached_all_passed(self):
        self.assertEqual(self.result.phase_reached, "ALL_PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# (B) LED circuit
# ══════════════════════════════════════════════════════════════════════════════

class TestLEDCircuitPipeline(unittest.TestCase):
    """Full pipeline on data/led_circuit.json — expects LED_MISSING_RESISTOR suggestion."""

    def setUp(self):
        self.result = run_pipeline(_fixture("led_circuit.json"))

    def test_led_suggestion_present(self):
        pattern_ids = [s.pattern_id for s in self.result.suggestions]
        self.assertIn("LED_MISSING_RESISTOR", pattern_ids)

    def test_suggestion_type_add_component(self):
        led_s = next(s for s in self.result.suggestions if s.pattern_id == "LED_MISSING_RESISTOR")
        self.assertEqual(led_s.type, "ADD_COMPONENT")
        self.assertEqual(led_s.component, "resistor")

    def test_suggestion_targets_led(self):
        led_s = next(s for s in self.result.suggestions if s.pattern_id == "LED_MISSING_RESISTOR")
        self.assertTrue(any("D" in cid for cid in led_s.target_component_ids))

    def test_circuit_still_passes_validation(self):
        """LED circuit has no missing ground or topology errors — validation should be clean."""
        error_issues = [i for i in self.result.issues if i.severity == "error"]
        self.assertEqual(len(error_issues), 0)

    def test_can_simulate_true_despite_suggestion(self):
        """Suggestions must NEVER mark a circuit as un-simulatable."""
        self.assertTrue(self.result.can_simulate)


# ══════════════════════════════════════════════════════════════════════════════
# (C) Op-amp circuit
# ══════════════════════════════════════════════════════════════════════════════

class TestOpAmpCircuitPipeline(unittest.TestCase):
    """Full pipeline on data/opamp_circuit.json — expects OPAMP_MISSING_POWER suggestions."""

    def setUp(self):
        self.result = run_pipeline(_fixture("opamp_circuit.json"))

    def test_opamp_power_suggestion_present(self):
        pattern_ids = [s.pattern_id for s in self.result.suggestions]
        self.assertIn("OPAMP_MISSING_POWER", pattern_ids)

    def test_power_suggestion_recommends_component(self):
        power_s = [s for s in self.result.suggestions if s.pattern_id == "OPAMP_MISSING_POWER"]
        components_suggested = {s.component for s in power_s}
        # At least one of the suggestions should be voltage_source or ground
        self.assertTrue(components_suggested & {"voltage_source", "ground"})

    def test_suggestions_do_not_alter_status(self):
        """Status is determined by validation only — suggestions are observers."""
        d = self.result.to_dict()
        self.assertIn(d["status"], ("success", "warning", "error"))

    def test_feedback_suggestion_may_be_present(self):
        """Op-amp without feedback → OPAMP_MISSING_FEEDBACK may also fire."""
        # Not mandatory (depends on output wiring), just verify shape if present
        fb = [s for s in self.result.suggestions if s.pattern_id == "OPAMP_MISSING_FEEDBACK"]
        for s in fb:
            self.assertEqual(s.type, "ADD_CONNECTION")


# ══════════════════════════════════════════════════════════════════════════════
# (D) API response shape (regression / contract)
# ══════════════════════════════════════════════════════════════════════════════

class TestAPIResponseShape(unittest.TestCase):
    """Verify to_dict() has all expected keys — no backward-compat regressions."""

    def setUp(self):
        self.d = run_pipeline(_fixture("valid_circuit.json")).to_dict()

    # Existing keys (must NOT be removed)
    def test_has_status(self):           self.assertIn("status",        self.d)
    def test_has_circuit_id(self):       self.assertIn("circuit_id",    self.d)
    def test_has_phase_reached(self):    self.assertIn("phase_reached", self.d)
    def test_has_issues_count(self):     self.assertIn("issues_count",  self.d)
    def test_has_issues(self):           self.assertIn("issues",        self.d)
    def test_has_graph(self):            self.assertIn("graph",         self.d)
    def test_has_metadata(self):         self.assertIn("metadata",      self.d)
    def test_metadata_has_rules_run(self):
        self.assertIn("rules_run", self.d["metadata"])

    # New keys
    def test_has_can_simulate(self):        self.assertIn("can_simulate",      self.d)
    def test_has_suggestions(self):         self.assertIn("suggestions",       self.d)
    def test_has_suggestions_count(self):   self.assertIn("suggestions_count", self.d)
    def test_metadata_has_patterns_run(self):
        self.assertIn("patterns_run", self.d["metadata"])


# ══════════════════════════════════════════════════════════════════════════════
# (E) Edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases(unittest.TestCase):

    def _run(self, data: dict) -> PipelineResult:
        path = _write_circuit(data)
        try:
            return run_pipeline(path)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_single_component_circuit(self):
        """A circuit with only 1 component — engine should not crash."""
        data = {
            "circuit_id": "single-comp",
            "component_templates": [
                {"id": "resistor", "name": "Resistor", "category": "passive",
                 "pins_template": [{"name": "p1", "type": "passive"}, {"name": "p2", "type": "passive"}],
                 "default_pins": 2, "property_schema": {}}
            ],
            "components": [
                {"id": "R1", "type": "resistor", "circuit_id": "single-comp",
                 "properties": {"resistance": "1000"}, "metadata": {}}
            ],
            "nets": [],
        }
        result = self._run(data)
        self.assertIn(result.status, ("success", "warning", "error"))
        # suggestions is always a list
        self.assertIsInstance(result.suggestions, list)

    def test_multiple_overlapping_patterns(self):
        """LED + voltage divider in the same circuit — both patterns can fire."""
        data = _minimal_circuit("overlap-test")
        # Add LED template
        data["component_templates"].append({
            "id": "led", "name": "LED", "category": "led",
            "pins_template": [{"name": "anode", "type": "passive"}, {"name": "cathode", "type": "passive"}],
            "default_pins": 2, "property_schema": {},
        })
        # Add second resistor (divider) + LED
        data["components"].extend([
            {"id": "R2", "type": "resistor", "circuit_id": "overlap-test", "properties": {"resistance": "10k"}, "metadata": {}},
            {"id": "D1", "type": "led",      "circuit_id": "overlap-test", "properties": {}, "metadata": {}},
        ])
        # Divider: R1 → mid → R2 → GND (existing R1 repurposed)
        data["nets"] = [
            {"id": "n1", "circuit_id": "overlap-test", "wire_type": "signal",
             "endpoints": [{"component_id": "V1", "pin_name": "positive"}, {"component_id": "R1", "pin_name": "p1"},
                           {"component_id": "D1", "pin_name": "anode"}], "properties": {}},
            {"id": "n_mid", "circuit_id": "overlap-test", "wire_type": "signal",
             "endpoints": [{"component_id": "R1", "pin_name": "p2"}, {"component_id": "R2", "pin_name": "p1"}], "properties": {}},
            {"id": "n_low", "circuit_id": "overlap-test", "wire_type": "signal",
             "endpoints": [{"component_id": "R2", "pin_name": "p2"}, {"component_id": "V1", "pin_name": "negative"},
                           {"component_id": "D1", "pin_name": "cathode"}, {"component_id": "G1", "pin_name": "gnd"}], "properties": {}},
        ]
        result = self._run(data)
        pattern_ids = {s.pattern_id for s in result.suggestions}
        # At least one pattern must fire (LED or divider)
        self.assertTrue(len(pattern_ids) >= 1)

    def test_invalid_circuit_still_produces_suggestions_structure(self):
        """A circuit with validation errors must still return a valid suggestions list."""
        data = {
            "circuit_id": "bad-circuit",
            "component_templates": [
                {"id": "dc_voltage_source", "name": "VS", "category": "source",
                 "pins_template": [{"name": "positive", "type": "output"}, {"name": "negative", "type": "output"}],
                 "default_pins": 2, "property_schema": {}},
                {"id": "led", "name": "LED", "category": "led",
                 "pins_template": [{"name": "anode", "type": "passive"}, {"name": "cathode", "type": "passive"}],
                 "default_pins": 2, "property_schema": {}},
            ],
            "components": [
                {"id": "V1", "type": "dc_voltage_source", "circuit_id": "bad-circuit",
                 "properties": {"voltage": "5"}, "metadata": {}},
                {"id": "D1", "type": "led", "circuit_id": "bad-circuit", "properties": {}, "metadata": {}},
            ],
            "nets": [
                # D1.cathode is floating — topology error — BUT LED pattern should still be considered
                {"id": "n1", "circuit_id": "bad-circuit", "wire_type": "signal",
                 "endpoints": [{"component_id": "V1", "pin_name": "positive"}, {"component_id": "D1", "pin_name": "anode"}],
                 "properties": {}},
                {"id": "n2", "circuit_id": "bad-circuit", "wire_type": "signal",
                 "endpoints": [{"component_id": "V1", "pin_name": "negative"}], "properties": {}},
            ],
        }
        result = self._run(data)
        self.assertIn(result.status, ("error", "warning"))
        self.assertIsInstance(result.suggestions, list)
        d = result.to_dict()
        self.assertIn("suggestions", d)


# ══════════════════════════════════════════════════════════════════════════════
# (F) Regression — existing suggested_fix still present on ValidationIssue
# ══════════════════════════════════════════════════════════════════════════════

class TestRegressionSuggestedFix(unittest.TestCase):
    """
    The frontend parseSuggestions.js depends on suggested_fix inside each issue.
    This must remain in the response forever (backward compat).
    """

    def _run_with_issues(self) -> dict:
        """Return a to_dict() result that contains at least one validation issue."""
        data = {
            "circuit_id": "regression-test",
            "component_templates": [
                {"id": "resistor", "name": "Resistor", "category": "passive",
                 "pins_template": [{"name": "p1", "type": "passive"}, {"name": "p2", "type": "passive"}],
                 "default_pins": 2, "property_schema": {}},
            ],
            "components": [
                {"id": "R1", "type": "resistor", "circuit_id": "regression-test",
                 "properties": {"resistance": "0"}, "metadata": {}},
            ],
            "nets": [],
        }
        path = _write_circuit(data)
        try:
            return run_pipeline(path).to_dict()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_validation_issue_contains_suggested_fix(self):
        d = self._run_with_issues()
        for issue in d.get("issues", []):
            self.assertIn("suggested_fix", issue, "suggested_fix missing from ValidationIssue dict")

    def test_validation_issue_contains_error_code(self):
        d = self._run_with_issues()
        for issue in d.get("issues", []):
            self.assertIn("error_code", issue)

    def test_validation_issue_contains_severity(self):
        d = self._run_with_issues()
        for issue in d.get("issues", []):
            self.assertIn("severity", issue)
            self.assertIn(issue["severity"], ("error", "warning"))


# ══════════════════════════════════════════════════════════════════════════════
# (G) PatternEngine isolation — suggestions never alter validity
# ══════════════════════════════════════════════════════════════════════════════

class TestPatternEngineIsolation(unittest.TestCase):
    """The Pattern Engine must observe, never decide."""

    def test_suggestions_do_not_change_status_on_valid_circuit(self):
        result = run_pipeline(_fixture("led_circuit.json"))
        # LED circuit is structurally valid — patterns fire but status stays ok
        self.assertIn(result.status, ("success", "warning"))
        self.assertGreater(len(result.suggestions), 0)

    def test_can_simulate_false_only_from_validation_errors(self):
        """can_simulate must reflect validation issues, not patterns."""
        result = run_pipeline(_fixture("valid_circuit.json"))
        # No errors → can simulate
        self.assertTrue(result.can_simulate)
        # Verify property derives from issues, not suggestions
        has_error = any(i.severity == "error" for i in result.issues)
        self.assertEqual(result.can_simulate, not has_error)

    def test_pattern_engine_result_is_list(self):
        result = run_pipeline(_fixture("valid_circuit.json"))
        self.assertIsInstance(result.suggestions, list)

    def test_suggestion_to_dict_has_required_keys(self):
        result = run_pipeline(_fixture("led_circuit.json"))
        for s in result.suggestions:
            d = s.to_dict()
            for key in ("pattern_id", "type", "component", "reason",
                        "confidence", "priority", "target_component_ids"):
                self.assertIn(key, d, f"Missing key '{key}' in suggestion dict")


if __name__ == "__main__":
    unittest.main()
