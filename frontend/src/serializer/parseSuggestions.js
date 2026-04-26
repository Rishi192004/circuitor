import { COMPONENT_LIBRARY } from '../constants/components.js'

const PIN_OFFSETS = {
  resistor:       { p1: { x: -40, y: 0 }, p2: { x: 40, y: 0 } },
  capacitor:      { p1: { x: -40, y: 0 }, p2: { x: 40, y: 0 } },
  dc_voltage_source: { positive: { x: 0, y: -40 }, negative: { x: 0, y: 40 } },
  ground:         { gnd: { x: 0, y: 0 } }
}

const ACTION_MAP = {
  "wire_pin":    "resistor",
  "add_ground":  "ground",
  "add_resistor":"resistor",
  "add_source":  "dc_voltage_source",
  "break_short": "resistor",
  "break_loop":  "resistor"
}

// Basic collision check against instances
function isOccupied(instances, x, y) {
  return instances.some(inst => inst.position.x === x && inst.position.y === y)
}

export function parseSuggestionsFromResult(pipelineResult, instances) {
  if (!pipelineResult || !pipelineResult.issues) return []

  const suggestions = []
  let suggestionCount = 0

  pipelineResult.issues.forEach(issue => {
    const fix = issue.suggested_fix
    const target = issue.target
    if (!fix || !target) return

    const action = fix.action
    const compType = ACTION_MAP[action]
    if (!compType) return // Not actionable with a ghost

    let compId = target.component_id
    let pinName = target.pin_name

    // Special case for global issues that suggest adding components
    if (target.type === 'global') {
      if (action === 'add_ground') {
        const source = instances.find(i => i.type === 'dc_voltage_source')
        if (source) {
          compId = source.id
          pinName = 'negative'
        }
      }
      // Fallback for any global issue if not resolved above
      if (!compId && instances.length > 0) {
        compId = instances[0].id
        const lib = COMPONENT_LIBRARY[instances[0].type]
        pinName = Object.keys(lib.pins)[0]
      }
    }

    if (!compId || !pinName) return

    const inst = instances.find(i => i.id === compId)
    if (!inst) return

    const offset = PIN_OFFSETS[inst.type]?.[pinName]
    if (!offset) return

    // Absolute position of the target pin
    const pinX = inst.position.x + offset.x
    const pinY = inst.position.y + offset.y

    // Try placing 60px BELOW (y + 60), if occupied try RIGHT, LEFT, ABOVE
    let gx = pinX
    let gy = pinY + 60

    if (isOccupied(instances, gx, gy)) {
      gx = pinX + 60; gy = pinY;
      if (isOccupied(instances, gx, gy)) {
        gx = pinX - 60; gy = pinY;
        if (isOccupied(instances, gx, gy)) {
          gx = pinX; gy = pinY - 60;
        }
      }
    }

    suggestions.push({
      id: `suggestion_${++suggestionCount}`,
      action: action,
      component_type: compType,
      attach_to: `${compId}.${pinName}`,
      position: { x: gx, y: gy },
      focused: false
    })
  })

  // Focus the first suggestion by default
  if (suggestions.length > 0) {
    suggestions[0].focused = true
  }

  return suggestions
}
