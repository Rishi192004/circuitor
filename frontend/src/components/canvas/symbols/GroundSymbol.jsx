import React from 'react'

/** LTSpice-style ground: pin line + three descending horizontal bars */
export default function GroundSymbol() {
  return (
    <g className="component-body">
      {/* Pin lead */}
      <line x1="0" y1="-16" x2="0" y2="0" />
      {/* Tier 1 (widest) */}
      <line x1="-13" y1="0"  x2="13" y2="0" />
      {/* Tier 2 */}
      <line x1="-8"  y1="6"  x2="8"  y2="6" />
      {/* Tier 3 */}
      <line x1="-4"  y1="12" x2="4"  y2="12" />
    </g>
  )
}
