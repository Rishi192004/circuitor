# Circuit Simulation Engine

A clean, minimal, production-oriented Python project for building a circuit simulation engine.

## Overview
This engine parses circuit definitions from JSON, builds a representative graph of the components and nets, and performs basic validation. It is designed to be easily extensible for netlist generation and AI integrations.

## Folder Structure
Follows clean architecture principles separating models, parsing, graph building, and validation logic.

## Usage
Run the main script:
```bash
python src/main.py
```

Run tests:
```bash
python -m unittest discover tests
```
