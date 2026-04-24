from abc import ABC, abstractmethod
from src.models.circuit import Circuit

class ValidationRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def validate(self, circuit: Circuit) -> bool:
        pass

class FloatingPinRule(ValidationRule):
    @property
    def name(self) -> str:
        return "Floating Pin Check"
        
    def validate(self, circuit: Circuit) -> bool:
        # Basic implementation: Check if any component has pins not connected to any net
        # (Omitted full logic for brevity, returning True for now as per "empty for now" requirement)
        return True
