import React from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'
import { COMPONENT_LIBRARY, getPinAbsolutePosition } from '../../constants/components.js'
import ResistorSymbol from './symbols/ResistorSymbol.jsx'
import CapacitorSymbol from './symbols/CapacitorSymbol.jsx'
import VoltageSourceSymbol from './symbols/VoltageSourceSymbol.jsx'
import GroundSymbol from './symbols/GroundSymbol.jsx'

const SYMBOLS = {
  resistor: ResistorSymbol,
  capacitor: CapacitorSymbol,
  dc_voltage_source: VoltageSourceSymbol,
  ground: GroundSymbol,
}

export default function GhostNode({ suggestion }) {
  const { instances } = useCircuitStore()
  
  const type = suggestion.component_type
  const lib = COMPONENT_LIBRARY[type]
  if (!lib) return null

  const Symbol = SYMBOLS[type]
  const { x, y } = suggestion.position
  const isFocused = suggestion.focused

  const [targetId, targetPin] = suggestion.attach_to.split('.')
  const targetInstance = instances.find(i => i.id === targetId)
  let line = null

  if (targetInstance) {
    const targetPos = getPinAbsolutePosition(targetInstance, targetPin)
    const firstPinName = Object.keys(lib.pins)[0]
    const ghostPinOffset = lib.pins[firstPinName]
    const ghostPinPos = { x: x + ghostPinOffset.x, y: y + ghostPinOffset.y }

    line = (
      <path
        d={`M ${targetPos.x} ${targetPos.y} L ${ghostPinPos.x} ${ghostPinPos.y}`}
        stroke="var(--lt-blue)"
        strokeWidth="2"
        strokeDasharray="4 4"
        fill="none"
        pointerEvents="none"
      />
    )
  }

  const opacity = isFocused ? 0.65 : 0.35
  const glow = isFocused ? '#00e5ff' : '#4fc3f7'

  return (
    <g>
      {line}
      <g
        className="ghost-node"
        transform={`translate(${x}, ${y})`}
        style={{
          opacity,
          pointerEvents: 'none',
          strokeDasharray: '6 3',
          filter: `drop-shadow(0 0 6px ${glow})`
        }}
      >
        {Symbol && <Symbol />}
        
        {isFocused && (
          <text
            x="0"
            y="-30"
            textAnchor="middle"
            fill="var(--lt-blue)"
            style={{ fontSize: '10px', fontWeight: 'bold', textShadow: '0 0 4px #000' }}
          >
            Tab to add {lib.label}
          </text>
        )}
      </g>
    </g>
  )
}
