import logging
from typing import List
from src.models.circuit import Circuit
from src.models.hint import SimulationHint
from src.hints.base import Hint

logger = logging.getLogger(__name__)

class SimulationHintEngine:
    """
    Orchestrates circuit simulation hint detection.
    """

    def __init__(self, hints: List[Hint]) -> None:
        self._hints = hints

    def run(self, circuit: Circuit) -> List[SimulationHint]:
        """
        Run all registered hints and return the results.
        """
        all_hints: List[SimulationHint] = []

        for hint in self._hints:
            try:
                results = hint.check(circuit)
                if results:
                    logger.info("Hint '%s' fired %d result(s).", hint.hint_id, len(results))
                    all_hints.extend(results)
            except Exception as exc:
                logger.error("Hint '%s' raised an error: %s", hint.hint_id, exc, exc_info=True)

        return all_hints
