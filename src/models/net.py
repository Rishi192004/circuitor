from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class PinConnection:
    component_id: str
    pin_name: str

    def __str__(self) -> str:
        return f"{self.component_id}.{self.pin_name}"

@dataclass
class Net:
    id: str
    circuit_id: str
    wire_type: str
    endpoints: List[PinConnection]
    properties: Dict[str, Any]
