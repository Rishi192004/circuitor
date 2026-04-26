import { COMPONENT_LIBRARY, getPinTemplate } from '../constants/components.js'

/**
 * toBackendFormat — converts the frontend's internal circuitState
 * (spec format) into the Python engine's expected Circuit JSON schema.
 *
 * Frontend format:
 *   nets[].pins = ["R1.p1", "V1.positive"]   ← "ComponentId.pinName" strings
 *
 * Backend format:
 *   nets[].endpoints = [{ component_id, pin_name }]
 */
export function toBackendFormat(circuitState) {
  const { circuit_id, templates, instances, nets } = circuitState

  // Map each template to the full component_template object the backend expects
  const component_templates = templates.map(tmpl => {
    const lib = COMPONENT_LIBRARY[tmpl.type]
    return {
      id: tmpl.type,
      name: lib?.label ?? tmpl.type,
      category: lib?.category ?? 'passive',
      pins_template: getPinTemplate(tmpl.type),
      default_pins: tmpl.pins.length,
      property_schema: {},
    }
  })

  // Map instances → components (backend name for placed instances)
  const components = instances.map(inst => ({
    id: inst.id,
    type: inst.type,
    properties: inst.properties ?? {},
    // Backend ignores metadata but we pass position for completeness
    metadata: {
      x: inst.position?.x ?? 0,
      y: inst.position?.y ?? 0,
    },
  }))

  // Translate "R1.p1" strings → { component_id: "R1", pin_name: "p1" } objects
  const backendNets = nets.map(net => ({
    id: net.id,
    endpoints: (net.pins ?? []).map(pinStr => {
      const dotIdx = pinStr.indexOf('.')
      if (dotIdx === -1) return { component_id: pinStr, pin_name: '' }
      return {
        component_id: pinStr.slice(0, dotIdx),
        pin_name:     pinStr.slice(dotIdx + 1),
      }
    }),
  }))

  return {
    circuit_id,
    component_templates,
    components,
    nets: backendNets,
  }
}
