import unittest
import json
import os
import tempfile
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.orchestrator.circuit_orchestrator import CircuitOrchestrator

class TestNoLoadHint(unittest.TestCase):
    def setUp(self):
        self.orchestrator = CircuitOrchestrator()

    def test_voltage_source_no_load_fires_hint(self):
        """
        Verify that a voltage source connected only to GND (no load) fires a hint.
        """
        circuit_data = {
            "circuit_id": "test_hint_fire",
            "component_templates": [
                {
                    "id": "dc_voltage_source", "name": "DC Voltage Source", "category": "source",
                    "pins_template": [{"name": "positive", "type": "output"}, {"name": "negative", "type": "output"}]
                },
                {
                    "id": "ground", "name": "Ground", "category": "reference",
                    "pins_template": [{"name": "gnd", "type": "passive"}]
                }
            ],
            "components": [
                {"id": "V1", "type": "dc_voltage_source", "properties": {"voltage": "5V"}},
                {"id": "G1", "type": "ground", "properties": {}}
            ],
            "nets": [
                {"id": "net1", "endpoints": [
                    {"component_id": "V1", "pin_name": "positive"}
                ]},
                {"id": "net2", "endpoints": [
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
            
            # Should have exactly 1 hint
            hint_ids = [h["hintId"] for h in res_dict["hints"]]
            self.assertIn("NO_LOAD_SOURCE", hint_ids)
            self.assertEqual(len(res_dict["errors"]), 0)
            
            print("Hint Fire Test Passed: No-load source detected.")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_voltage_source_with_load_silent(self):
        """
        Verify that a voltage source with a resistor load does NOT fire a hint.
        """
        circuit_data = {
            "circuit_id": "test_hint_silent",
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
                    "id": "ground", "name": "Ground", "category": "reference",
                    "pins_template": [{"name": "gnd", "type": "passive"}]
                }
            ],
            "components": [
                {"id": "V1", "type": "dc_voltage_source", "properties": {"voltage": "5V"}},
                {"id": "R1", "type": "resistor", "properties": {"resistance": "1k"}},
                {"id": "G1", "type": "ground", "properties": {}}
            ],
            "nets": [
                {"id": "net1", "endpoints": [
                    {"component_id": "V1", "pin_name": "positive"},
                    {"component_id": "R1", "pin_name": "p1"}
                ]},
                {"id": "net2", "endpoints": [
                    {"component_id": "R1", "pin_name": "p2"},
                    {"component_id": "G1", "pin_name": "gnd"}
                ]},
                {"id": "net3", "endpoints": [
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
            
            # Should have 0 hints
            self.assertEqual(len(res_dict["hints"]), 0)
            
            print("Hint Silent Test Passed: Source with load is clean.")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
