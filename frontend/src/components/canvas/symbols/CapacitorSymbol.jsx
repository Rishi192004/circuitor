import React from 'react'

/** LTSpice-style capacitor: leads + two parallel plates */
export default function CapacitorSymbol() {
  return (
    <g className="component-body">
      {/* Left lead */}
      <line x1="-32" y1="0" x2="-4" y2="0" />
      {/* Left plate */}
      <line x1="-4" y1="-11" x2="-4" y2="11" />
      {/* Right plate */}
      <line x1="4" y1="-11" x2="4" y2="11" />
      {/* Right lead */}
      <line x1="4" y1="0" x2="32" y2="0" />
    </g>
  )
}
