from dataclasses import dataclass, field
from typing import Dict, List, Optional
from src.models.component import Component, ComponentTemplate
from src.models.net import Net

@dataclass
class Circuit:
    id: str
    component_templates: Dict[str, ComponentTemplate]
    components: Dict[str, Component]
    nets: Dict[str, Net]
    graph: Optional[Dict[str, List[str]]] = field(default=None, repr=False)
