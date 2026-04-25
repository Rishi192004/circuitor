import re
import logging
from typing import Any
from src.models.circuit import Circuit

logger = logging.getLogger(__name__)

class ValueNormalizer:
    # SI prefixes mapping to their multipliers
    MULTIPLIERS = {
        'T': 1e12,   # Tera
        'G': 1e9,    # Giga
        'M': 1e6,    # Mega
        'k': 1e3,    # kilo
        'm': 1e-3,   # milli
        'u': 1e-6,   # micro
        'µ': 1e-6,   # micro (alt)
        'n': 1e-9,   # nano
        'p': 1e-12,  # pico
        'f': 1e-15   # femto
    }

    # Regex to match a number followed by an optional SI prefix and optional text
    # Example: "10", "10k", "5.5uF", "2k ohm", "100 ohm"
    PATTERN = re.compile(r'^([+-]?\d*\.?\d+)\s*([A-Za-zµ]*)(?:\s.*)?$')

    @classmethod
    def normalize_value(cls, value: Any) -> Any:
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            value = value.strip()
            match = cls.PATTERN.match(value)
            if match:
                num_str, suffix = match.groups()
                num = float(num_str)
                
                # Check for standard multipliers in the first character of the suffix
                if suffix:
                    # Sometimes 'meg' is used instead of M in SPICE
                    if suffix.lower().startswith('meg'):
                        return num * 1e6
                        
                    first_char = suffix[0]
                    if first_char in cls.MULTIPLIERS:
                        return num * cls.MULTIPLIERS[first_char]
                
                return num
                
        return value

    @classmethod
    def normalize_circuit(cls, circuit: Circuit):
        logger.info("Normalizing component properties...")
        normalized_count = 0
        for comp_id, comp in circuit.components.items():
            for prop_name, prop_value in comp.properties.items():
                normalized_val = cls.normalize_value(prop_value)
                if normalized_val != prop_value:
                    comp.properties[prop_name] = normalized_val
                    logger.debug(f"Normalized {comp_id}.{prop_name}: '{prop_value}' -> {normalized_val}")
                    normalized_count += 1
        
        logger.info(f"Normalized {normalized_count} property values to standard floats.")
