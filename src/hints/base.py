from abc import ABC, abstractmethod
from typing import List
from src.models.circuit import Circuit
from src.models.hint import SimulationHint

class Hint(ABC):
    """
    Abstract base class for all simulation hints.
    """

    @property
    @abstractmethod
    def hint_id(self) -> str:
        """Unique identifier for this hint."""

    @abstractmethod
    def check(self, circuit: Circuit) -> List[SimulationHint]:
        """
        Check the circuit for this hint's condition.
        Returns a list of SimulationHint objects if conditions match.
        """
