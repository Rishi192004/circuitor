import React from 'react'

export default function OpAmpSymbol() {
  return (
    <g className="component-body">
      {/* Triangle Body */}
      <path d="M -30 -35 L 30 0 L -30 35 Z" />

      {/* Internal + and - signs */}
      <text x="-22" y="-14" fontSize="14" textAnchor="middle" fill="var(--lt-blue)" style={{ userSelect: 'none' }}>+</text>
      <text x="-22" y="24" fontSize="14" textAnchor="middle" fill="var(--lt-blue)" style={{ userSelect: 'none' }}>-</text>

      {/* Pin Lines (to reach the hitboxes) */}
      {/* non_inverting (+) */}
      <line x1="-40" y1="-20" x2="-30" y2="-20" />
      {/* inverting (-) */}
      <line x1="-40" y1="20" x2="-30" y2="20" />
      {/* output */}
      <line x1="30" y1="0" x2="40" y2="0" />
      {/* vcc */}
      <line x1="0" y1="-40" x2="0" y2="-17.5" />
      {/* vee */}
      <line x1="0" y1="40" x2="0" y2="17.5" />
    </g>
  )
}
