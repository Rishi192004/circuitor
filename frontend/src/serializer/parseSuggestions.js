import { COMPONENT_LIBRARY } from '../constants/components.js'

const PIN_OFFSETS = {
  resistor:       { p1: { x: -40, y: 0 }, p2: { x: 40, y: 0 } },
  capacitor:      { p1: { x: -40, y: 0 }, p2: { x: 40, y: 0 } },
  dc_voltage_source: { positive: { x: 0, y: -40 }, negative: { x: 0, y: 40 } },
  ground:         { gnd: { x: 0, y: 0 } },
  op_amp:         { non_inverting: { x: -40, y: -20 }, inverting: { x: -40, y: 20 }, output: { x: 40, y: 0 }, vcc: { x: 0, y: -40 }, vee: { x: 0, y: 40 } },
  led:            { anode: { x: -32, y: 0 }, cathode: { x: 32, y: 0 } }
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

export function parseSuggestionsFromResult(analysisResult, instances) {
  if (!analysisResult || !analysisResult.ghostComponents) return []

  const suggestions = []
  let suggestionCount = 0

  analysisResult.ghostComponents.forEach(gc => {
    const action = gc.metadata?.action || "add_component"
    const compType = gc.type
    const attachTo = gc.metadata?.attach_to || gc.metadata?.target_pin // Adjust based on backend metadata
    
    let compId, pinName
    if (attachTo && attachTo.includes('.')) {
      [compId, pinName] = attachTo.split('.')
    } else if (gc.metadata?.target_component_id) {
       compId = gc.metadata.target_component_id
       pinName = gc.metadata.target_pin_name || Object.keys(COMPONENT_LIBRARY[instances.find(i => i.id === compId)?.type]?.pins || {})[0]
    }

    // Fallback for global issues (like missing ground)
    if (!compId && instances.length > 0) {
      // Find a suitable source to attach a ground to, or just the first component
      const source = instances.find(i => i.type === 'dc_voltage_source')
      compId = source ? source.id : instances[0].id
      const lib = COMPONENT_LIBRARY[instances.find(i => i.id === compId).type]
      pinName = source ? 'negative' : Object.keys(lib.pins)[0]
    }

    if (!compId || !pinName) return

    const inst = instances.find(i => i.id === compId)
    if (!inst) return

    const offset = PIN_OFFSETS[inst.type]?.[pinName]
    if (!offset) return

    const pinX = inst.position.x + offset.x
    const pinY = inst.position.y + offset.y

    // Layout logic (fanning out suggestions)
    let gx = pinX
    let gy = pinY + 60
    let attempts = 0
    while (isOccupied(instances, gx, gy) && attempts < 4) {
      if (attempts === 0) { gx = pinX + 60; gy = pinY }
      else if (attempts === 1) { gx = pinX - 60; gy = pinY }
      else if (attempts === 2) { gx = pinX; gy = pinY - 60 }
      attempts++
    }

    suggestions.push({
      id: `suggestion_${++suggestionCount}`,
      action: action,
      component_type: compType,
      attach_to: `${compId}.${pinName}`,
      position: { x: gx, y: gy },
      reason: gc.reason,
      focused: false
    })
  })

  // Focus the first suggestion by default
  if (suggestions.length > 0) {
    suggestions[0].focused = true
  }

  return suggestions
}
