import json
import logging
from typing import Dict, Any
from src.models.component import Component, ComponentTemplate, PinTemplate
from src.models.net import Net, PinConnection
from src.models.circuit import Circuit

logger = logging.getLogger(__name__)

class CircuitParser:
    @staticmethod
    def parse_json(filepath: str) -> Circuit:
        logger.info(f"Loading circuit from {filepath}")
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        circuit_id = data.get("circuit_id", "")
        
        # Parse component templates
        templates = {}
        for tmpl_data in data.get("component_templates", []):
            pins_template = [
                PinTemplate(name=p["name"], type=p["type"])
                for p in tmpl_data.get("pins_template", [])
            ]
            template = ComponentTemplate(
                id=tmpl_data["id"],
                name=tmpl_data.get("name", ""),
                category=tmpl_data.get("category", ""),
                pins_template=pins_template,
                default_pins=tmpl_data.get("default_pins", 0),
                property_schema=tmpl_data.get("property_schema", {})
            )
            templates[template.id] = template
            
        # Parse components
        components = {}
        for comp_data in data.get("components", []):
            comp = Component(
                id=comp_data["id"],
                type=comp_data["type"],
                circuit_id=comp_data.get("circuit_id", circuit_id),
                properties=comp_data.get("properties", {}),
                metadata=comp_data.get("metadata", {})
            )
            components[comp.id] = comp
            
        # Parse nets
        nets = {}
        for net_data in data.get("nets", []):
            endpoints = [
                PinConnection(component_id=conn["component_id"], pin_name=conn["pin_name"])
                for conn in net_data.get("endpoints", [])
            ]
            net = Net(
                id=net_data["id"],
                circuit_id=net_data.get("circuit_id", circuit_id),
                wire_type=net_data.get("wire_type", ""),
                endpoints=endpoints,
                properties=net_data.get("properties", {})
            )
            nets[net.id] = net
            
        return Circuit(
            id=circuit_id,
            component_templates=templates,
            components=components,
            nets=nets
        )
