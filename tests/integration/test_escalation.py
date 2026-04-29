import unittest
import json
import os
import tempfile
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.orchestrator.circuit_orchestrator import CircuitOrchestrator

class TestPatternEscalation(unittest.TestCase):
    def setUp(self):
        self.orchestrator = CircuitOrchestrator()

    def test_led_no_resistor_escalates_to_error(self):
        """
        Verify that an LED with no resistor (LEDPattern) escalates to a 
        Validation error instead of a non-blocking suggestion.
        """
        circuit_data = {
            "circuit_id": "test_escalation",
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
                {"id": "G1", "type": "ground", "properties": {}}
            ],
            "nets": [
                # Net 1: V1+ to D1 Anode (Direct connection -> LEDPattern)
                {"id": "net1", "endpoints": [
                    {"component_id": "V1", "pin_name": "positive"},
                    {"component_id": "D1", "pin_name": "anode"}
                ]},
                # Net 2: D1 Cathode to V1- and Ground
                {"id": "net2", "endpoints": [
                    {"component_id": "D1", "pin_name": "cathode"},
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
            
            # The pattern should have escalated to an error
            self.assertFalse(res_dict["isSimulationReady"], "Circuit should NOT be ready (escalated to error)")
            
            # Check errors array
            error_codes = [e["errorCode"] for e in res_dict["errors"]]
            self.assertIn("LED_MISSING_RESISTOR", error_codes, "LEDPattern should be in errors array")
            
            # Check suggestions array (should NOT be there anymore as it's an error)
            suggestion_ids = [s["patternId"] for s in res_dict["suggestions"]]
            self.assertNotIn("LED_MISSING_RESISTOR", suggestion_ids, "Escalated pattern should not be in suggestions array")
            
            # Ghost components should STILL be there (UI still wants them)
            ghost_types = [g["type"] for g in res_dict["ghostComponents"]]
            self.assertIn("resistor", ghost_types)

            print("Escalation Test Passed: LED missing resistor escalated to fatal error.")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_led_with_resistor_no_pattern(self):
        """
        Verify that an LED WITH a resistor does not fire the pattern at all.
        """
        circuit_data = {
            "circuit_id": "test_no_escalation",
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
                {"id": "R1", "type": "resistor", "properties": {"resistance": "220"}},
                {"id": "D1", "type": "led", "properties": {}},
                {"id": "G1", "type": "ground", "properties": {}}
            ],
            "nets": [
                {"id": "net1", "endpoints": [
                    {"component_id": "V1", "pin_name": "positive"},
                    {"component_id": "R1", "pin_name": "p1"}
                ]},
                {"id": "net2", "endpoints": [
                    {"component_id": "R1", "pin_name": "p2"},
                    {"component_id": "D1", "pin_name": "anode"}
                ]},
                {"id": "net3", "endpoints": [
                    {"component_id": "D1", "pin_name": "cathode"},
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
            
            self.assertTrue(res_dict["isSimulationReady"])
            self.assertEqual(len(res_dict["errors"]), 0)
            self.assertEqual(len(res_dict["suggestions"]), 0)

            print("No Pattern Test Passed: LED with resistor is clean.")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
