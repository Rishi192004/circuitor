import React from 'react'
import { COMPONENT_LIBRARY } from '../../constants/components.js'
import ResistorSymbol from '../canvas/symbols/ResistorSymbol.jsx'
import CapacitorSymbol from '../canvas/symbols/CapacitorSymbol.jsx'
import VoltageSourceSymbol from '../canvas/symbols/VoltageSourceSymbol.jsx'
import GroundSymbol from '../canvas/symbols/GroundSymbol.jsx'
import OpAmpSymbol from '../canvas/symbols/OpAmpSymbol.jsx'
import LEDSymbol from '../canvas/symbols/LEDSymbol.jsx'

const SYMBOLS = {
  resistor: ResistorSymbol,
  capacitor: CapacitorSymbol,
  dc_voltage_source: VoltageSourceSymbol,
  ground: GroundSymbol,
  op_amp: OpAmpSymbol,
  led: LEDSymbol,
}

function SidebarPreview({ type }) {
  const Symbol = SYMBOLS[type]
  const lib = COMPONENT_LIBRARY[type]
  if (!Symbol) return null

  const halfW = (lib?.svgWidth ?? 64) / 2
  const halfH = (lib?.svgHeight ?? 40) / 2

  return (
    <svg
      className="sidebar__symbol"
      viewBox={`${-halfW} ${-halfH} ${halfW * 2} ${halfH * 2}`}
      preserveAspectRatio="xMidYMid meet"
    >
      <Symbol />
    </svg>
  )
}

export default function ComponentSidebar() {
  function onDragStart(e, type) {
    e.dataTransfer.setData('componentType', type)
    e.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <aside className="sidebar">
      <div className="sidebar__header">Components</div>
      {Object.entries(COMPONENT_LIBRARY).map(([type, lib]) => (
        <div
          key={type}
          id={`sidebar-${type}`}
          className="sidebar__item"
          draggable
          onDragStart={e => onDragStart(e, type)}
          title={`Drag to place ${lib.label}`}
        >
          <SidebarPreview type={type} />
          <div>
            <div className="sidebar__label">{lib.label}</div>
            <div className="sidebar__sublabel">{lib.symbol}</div>
          </div>
        </div>
      ))}
    </aside>
  )
}
