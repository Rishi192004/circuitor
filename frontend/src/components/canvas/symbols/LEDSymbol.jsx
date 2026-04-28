import React from 'react'

export default function LEDSymbol() {
  return (
    <g className="component-body">
      {/* Diode Triangle */}
      <path d="M -15 -15 L 10 0 L -15 15 Z" />
      {/* Cathode Line */}
      <line x1="10" y1="-15" x2="10" y2="15" />

      {/* Pin Lines */}
      <line x1="-32" y1="0" x2="-15" y2="0" />
      <line x1="10" y1="0" x2="32" y2="0" />

      {/* Light Rays */}
      <line x1="-5" y1="-18" x2="5" y2="-28" />
      <line x1="5" y1="-15" x2="15" y2="-25" />

      {/* Small arrows on rays */}
      <path d="M 3 -28 L 5 -28 L 5 -26" />
      <path d="M 13 -25 L 15 -25 L 15 -23" />
    </g>
  )
}
