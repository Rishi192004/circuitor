/**
 * COMPONENT_LIBRARY — visual + structural definition of every component type.
 * Drives the canvas SVG rendering and pin-offset math.
 */
export const COMPONENT_LIBRARY = {
  resistor: {
    label: 'Resistor',
    symbol: 'R',
    category: 'passive',
    svgWidth: 64,
    svgHeight: 24,
    pins: {
      p1: { x: -32, y: 0 },
      p2: { x:  32, y: 0 },
    },
    defaultProps: { resistance: '1k' },
  },
  capacitor: {
    label: 'Capacitor',
    symbol: 'C',
    category: 'passive',
    svgWidth: 64,
    svgHeight: 28,
    pins: {
      p1: { x: -32, y: 0 },
      p2: { x:  32, y: 0 },
    },
    defaultProps: { capacitance: '100n' },
  },
  dc_voltage_source: {
    label: 'Voltage Source',
    symbol: 'V',
    category: 'source',
    svgWidth: 44,
    svgHeight: 80,
    pins: {
      positive: { x: 0, y: -40 },
      negative: { x: 0, y:  40 },
    },
    defaultProps: { voltage: '5V' },
  },
  ground: {
    label: 'Ground',
    symbol: 'GND',
    category: 'reference',
    svgWidth: 32,
    svgHeight: 32,
    pins: {
      gnd: { x: 0, y: -16 },
    },
    defaultProps: {},
  },
}

/**
 * TEMPLATES — static constant that exactly matches the circuitState.templates
 * schema the backend expects. Always sent in full on every API call.
 * Pin type is 'output' for voltage sources; 'passive' for everything else.
 */
export const TEMPLATES = [
  {
    type: 'resistor',
    pins: ['p1', 'p2'],
    properties: { resistance: '1k' },
  },
  {
    type: 'capacitor',
    pins: ['p1', 'p2'],
    properties: { capacitance: '100n' },
  },
  {
    type: 'dc_voltage_source',
    pins: ['positive', 'negative'],
    properties: { voltage: '5V' },
  },
  {
    type: 'ground',
    pins: ['gnd'],
    properties: {},
  },
]

/**
 * Returns the pin template array format the backend expects inside component_templates.
 * Pin type is 'output' for sources; 'passive' for everything else.
 */
export function getPinTemplate(type) {
  const lib = COMPONENT_LIBRARY[type]
  if (!lib) return []
  const pinType = lib.category === 'source' ? 'output' : 'passive'
  return Object.keys(lib.pins).map(name => ({ name, type: pinType }))
}

/**
 * Given a placed instance and a pin name, returns absolute SVG canvas
 * coordinates of that pin. Works with both old {x,y} and new {position:{x,y}}.
 */
export function getPinAbsolutePosition(instance, pinName) {
  const lib = COMPONENT_LIBRARY[instance.type]
  // Support both old flat shape and new position-object shape
  const bx = instance.position?.x ?? instance.x ?? 0
  const by = instance.position?.y ?? instance.y ?? 0
  if (!lib) return { x: bx, y: by }
  const pinOffset = lib.pins[pinName]
  if (!pinOffset) return { x: bx, y: by }
  return { x: bx + pinOffset.x, y: by + pinOffset.y }
}
