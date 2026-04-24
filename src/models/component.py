from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class PinTemplate:
    name: str
    type: str

@dataclass
class ComponentTemplate:
    id: str
    name: str
    category: str
    pins_template: List[PinTemplate]
    default_pins: int
    property_schema: Dict[str, Any]

@dataclass
class Component:
    id: str
    type: str  # References ComponentTemplate.id
    circuit_id: str
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
