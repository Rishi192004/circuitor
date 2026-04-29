import unittest
import json
import os
import tempfile
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.orchestrator.circuit_orchestrator import CircuitOrchestrator

class TestCircuitOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = CircuitOrchestrator()

    def test_merged_result_error_and_suggestion(self):
        """
        Verifies that the orchestrator returns both validation errors and 
        pattern suggestions in a single unified result.
        """
        # Circuit setup:
        # 1. R1 has p2 floating -> E101 Error
        # 2. D1 connected directly to V1 -> LED_MISSING_RESISTOR Suggestion
        circuit_data = {
            "circuit_id": "test_merged_logic",
            "component_templates": [
                {
                    "id": "resistor", "name": "Resistor", "category": "passive",
                    "pins_template": [{"name": "p1", "type": "passive"}, {"name": "p2", "type": "passive"}]
                },
                {
                    "id": "dc_voltage_source", "name": "DC Voltage Source", "category": "source",
                    "pins_template": [{"name": "positive", "type": "output"}, {"name": "negative", "type": "output"}]
                },
                {
                    "id": "led", "name": "LED", "category": "led",
                    "pins_template": [{"name": "anode", "type": "passive"}, {"name": "cathode", "type": "passive"}]
                },
                {
                    "id": "ground", "name": "Ground", "category": "reference",
                    "pins_template": [{"name": "gnd", "type": "passive"}]
                }
            ],
            "components": [
                {"id": "V1", "type": "dc_voltage_source", "properties": {"voltage": "5V"}},
                {"id": "D1", "type": "led", "properties": {}},
                {"id": "R1", "type": "resistor", "properties": {"resistance": "1k"}},
                {"id": "G1", "type": "ground", "properties": {}}
            ],
            "nets": [
                # Net 1: V1+ to D1 Anode (Direct connection -> LEDPattern suggestion)
                {"id": "net1", "endpoints": [
                    {"component_id": "V1", "pin_name": "positive"},
                    {"component_id": "D1", "pin_name": "anode"}
                ]},
                # Net 2: R1 p1 to V1- and Ground (R1 p2 is left floating -> FloatingPin error)
                {"id": "net2", "endpoints": [
                    {"component_id": "R1", "pin_name": "p1"},
                    {"component_id": "V1", "pin_name": "negative"},
                    {"component_id": "G1", "pin_name": "gnd"}
                ]}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(circuit_data, tmp)
            tmp_path = tmp.name
        
        try:
            result = self.orchestrator.analyze(tmp_path)
            res_dict = result.to_dict()
            
            # 1. Verify structural integrity of the unified result
            self.assertIn("isSimulationReady", res_dict)
            self.assertIn("errors", res_dict)
            self.assertIn("warnings", res_dict)
            self.assertIn("suggestions", res_dict)
            self.assertIn("ghostComponents", res_dict)
            
            # 2. Verify Validation Logic
            self.assertFalse(res_dict["isSimulationReady"], "Circuit should not be ready due to errors")
            error_codes = [e["errorCode"] for e in res_dict["errors"]]
            self.assertIn("E101", error_codes, "Should detect FloatingPinRule error (E101)")
            self.assertIn("LED_MISSING_RESISTOR", error_codes, "Should detect escalated LED_MISSING_RESISTOR error")
            
            # 3. Verify Pattern Logic (Escalated patterns are moved out of suggestions)
            pattern_ids = [s["patternId"] for s in res_dict["suggestions"]]
            self.assertNotIn("LED_MISSING_RESISTOR", pattern_ids, "Escalated pattern should not be in suggestions")
            
            # 4. Verify Ghost Component mapping
            ghost_types = [g["type"] for g in res_dict["ghostComponents"]]
            self.assertIn("resistor", ghost_types, "Should have a ghost resistor suggested")
            
            print("Orchestrator Integration Test Passed: Merged result contains both errors and suggestions.")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
