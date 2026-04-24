from dataclasses import dataclass
from typing import Dict
from src.models.component import Component, ComponentTemplate
from src.models.net import Net

@dataclass
class Circuit:
    id: str
    component_templates: Dict[str, ComponentTemplate]
    components: Dict[str, Component]
    nets: Dict[str, Net]
