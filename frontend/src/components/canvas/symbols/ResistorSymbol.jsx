import React from 'react'

/** LTSpice-style resistor: leads + zigzag body */
export default function ResistorSymbol() {
  return (
    <g className="component-body">
      {/* Left lead */}
      <line x1="-32" y1="0" x2="-14" y2="0" />
      {/* Zigzag body */}
      <polyline points="-14,0 -11,-7 -7,7 -3,-7 1,7 5,-7 9,7 13,-7 14,0" />
      {/* Right lead */}
      <line x1="14" y1="0" x2="32" y2="0" />
    </g>
  )
}
