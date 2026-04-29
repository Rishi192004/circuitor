import React from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'
import { COMPONENT_LIBRARY, getPinAbsolutePosition } from '../../constants/components.js'
import ResistorSymbol from './symbols/ResistorSymbol.jsx'
import CapacitorSymbol from './symbols/CapacitorSymbol.jsx'
import VoltageSourceSymbol from './symbols/VoltageSourceSymbol.jsx'
import GroundSymbol from './symbols/GroundSymbol.jsx'
import OpAmpSymbol from './symbols/OpAmpSymbol.jsx'
import LEDSymbol from './symbols/LEDSymbol.jsx'

const SYMBOLS = {
  resistor: ResistorSymbol,
  capacitor: CapacitorSymbol,
  dc_voltage_source: VoltageSourceSymbol,
  ground: GroundSymbol,
  op_amp: OpAmpSymbol,
  led: LEDSymbol,
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

  const opacity = isFocused ? 0.7 : 0.4
  const glow = isFocused ? '#7c4dff' : '#448aff' // Purple for focus, blue for idle

  return (
    <g 
      style={{ cursor: 'pointer', pointerEvents: 'all' }}
      onClick={() => useCircuitStore.getState().acceptSuggestion(suggestion.id)}
    >
      {line}
      <g
        className="ghost-node"
        transform={`translate(${x}, ${y})`}
        style={{
          filter: `drop-shadow(0 0 8px ${glow})`,
          opacity: isFocused ? 0.8 : 'var(--ghost-opacity)'
        }}
      >
        <rect
          x="-30" y="-30" width="60" height="60"
          rx="4" fill="rgba(124, 77, 255, 0.05)"
          stroke={glow} strokeWidth="1"
        />
        
        {Symbol && <Symbol />}
        
        {/* "+" Add Icon Badge */}
        <g transform="translate(20, -20)">
          <circle r="7" fill={glow} />
          <text
            y="0.5" textAnchor="middle" dominantBaseline="middle"
            fill="white" style={{ fontSize: '12px', fontWeight: 'bold' }}
          >
            +
          </text>
        </g>

        {isFocused && (
          <g transform="translate(0, 45)">
            <rect 
              x="-60" y="-12" width="120" height="20" rx="4"
              fill="rgba(0,0,0,0.8)" 
            />
            <text
              textAnchor="middle"
              fill="white"
              style={{ fontSize: '10px', fontWeight: 'bold' }}
            >
              Click or Tab to place {lib.label}
            </text>
          </g>
        )}
      </g>
    </g>
  )
}
