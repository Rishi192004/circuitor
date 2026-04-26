import React from 'react'
import { COMPONENT_LIBRARY } from '../../constants/components.js'
import ResistorSymbol from '../canvas/symbols/ResistorSymbol.jsx'
import CapacitorSymbol from '../canvas/symbols/CapacitorSymbol.jsx'
import VoltageSourceSymbol from '../canvas/symbols/VoltageSourceSymbol.jsx'
import GroundSymbol from '../canvas/symbols/GroundSymbol.jsx'

const SYMBOLS = {
  resistor: ResistorSymbol,
  capacitor: CapacitorSymbol,
  dc_voltage_source: VoltageSourceSymbol,
  ground: GroundSymbol,
}

function SidebarPreview({ type }) {
  const Symbol = SYMBOLS[type]
  if (!Symbol) return null
  return (
    <svg className="sidebar__symbol" viewBox="-32 -20 64 40" preserveAspectRatio="xMidYMid meet">
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
