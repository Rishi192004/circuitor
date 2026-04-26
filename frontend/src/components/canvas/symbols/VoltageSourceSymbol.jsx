import React from 'react'

/** LTSpice-style voltage source: circle + +/- labels */
export default function VoltageSourceSymbol() {
  return (
    <g className="component-body">
      {/* Top lead (positive) */}
      <line x1="0" y1="-40" x2="0" y2="-22" />
      {/* Circle body */}
      <circle cx="0" cy="0" r="22" />
      {/* Positive symbol (top half) */}
      <line x1="0"  y1="-13" x2="0"  y2="-5" />
      <line x1="-4" y1="-9"  x2="4"  y2="-9" />
      {/* Negative symbol (bottom half) */}
      <line x1="-4" y1="9"   x2="4"  y2="9" />
      {/* Bottom lead (negative) */}
      <line x1="0" y1="22" x2="0" y2="40" />
    </g>
  )
}
