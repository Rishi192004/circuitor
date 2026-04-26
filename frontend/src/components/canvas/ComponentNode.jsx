import React from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'
import { COMPONENT_LIBRARY } from '../../constants/components.js'
import PinDot from './PinDot.jsx'
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

const LABEL_OFFSET = {
  resistor:          { ref: { x: 0, y: -16 }, val: { x: 0, y: -7  } },
  capacitor:         { ref: { x: 0, y: -18 }, val: { x: 0, y: -9  } },
  dc_voltage_source: { ref: { x: 26, y: -8 }, val: { x: 26, y: 4  } },
  ground:            { ref: { x: 0, y: 28  }, val: { x: 0, y: 38  } },
}

/**
 * Renders a single placed instance on the SVG canvas.
 * Receives `instance` with shape: { id, type, position:{x,y}, properties }
 */
export default function ComponentNode({ instance, svgRef }) {
  const {
    selectedId, highlightedIds,
    selectInstance, startWire, completeWire,
    wireInProgress,
  } = useCircuitStore()

  const lib = COMPONENT_LIBRARY[instance.type]
  if (!lib) return null

  const Symbol    = SYMBOLS[instance.type]
  const isSelected = selectedId === instance.id
  const { x, y }  = instance.position   // ← new shape

  // Highlight class from panel click
  const highlight       = highlightedIds.find(h => h.id === instance.id)
  const isHighlightError   = highlight?.severity === 'error'
  const isHighlightWarning = highlight?.severity === 'warning'

  let nodeClass = 'component-node'
  if (isSelected)         nodeClass += ' selected'
  if (isHighlightError)   nodeClass += ' highlighted-error'
  if (isHighlightWarning) nodeClass += ' highlighted-warning'

  const labelOff = LABEL_OFFSET[instance.type] ?? { ref: { x: 0, y: -18 }, val: { x: 0, y: -8 } }

  // ── Click: select (if not wiring) ──────────────────────────
  function handleGroupClick(e) {
    e.stopPropagation()
    if (wireInProgress) return
    selectInstance(instance.id)
  }

  // ── MouseDown: start drag-to-move ──────────────────────────
  let dragStart = null
  function onMouseDown(e) {
    if (wireInProgress) return
    if (e.button !== 0) return
    e.stopPropagation()
    selectInstance(instance.id)

    const svg = svgRef.current
    const pt  = svg.createSVGPoint()
    pt.x = e.clientX; pt.y = e.clientY
    const svgPt = pt.matrixTransform(svg.getScreenCTM().inverse())

    // Capture origin in SVG space
    dragStart = { mx: svgPt.x, my: svgPt.y, cx: x, cy: y }

    function onMove(me) {
      if (!dragStart) return
      const p = svg.createSVGPoint()
      p.x = me.clientX; p.y = me.clientY
      const sp = p.matrixTransform(svg.getScreenCTM().inverse())
      useCircuitStore.getState().moveInstance(
        instance.id,
        dragStart.cx + (sp.x - dragStart.mx),
        dragStart.cy + (sp.y - dragStart.my)
      )
    }
    function onUp() {
      dragStart = null
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  // First property value for the label (e.g. "1k", "5V")
  const propKey = Object.keys(instance.properties ?? {})[0]
  const propVal = propKey ? instance.properties[propKey] : null

  return (
    <g
      className={nodeClass}
      transform={`translate(${x}, ${y})`}
      onClick={handleGroupClick}
      onMouseDown={onMouseDown}
      id={`node-${instance.id}`}
    >
      {Symbol && <Symbol />}

      {/* Reference designator — LTSpice green */}
      <text
        className="component-label-ref"
        x={labelOff.ref.x}
        y={labelOff.ref.y}
        textAnchor="middle"
        dominantBaseline="auto"
      >
        {instance.id}
      </text>

      {/* Value label */}
      {propVal && (
        <text
          className="component-label-val"
          x={labelOff.val.x}
          y={labelOff.val.y}
          textAnchor="middle"
          dominantBaseline="auto"
        >
          {propVal}
        </text>
      )}

      {/* Pin dots */}
      {Object.entries(lib.pins).map(([pinName, offset]) => (
        <PinDot
          key={pinName}
          x={offset.x}
          y={offset.y}
          pinName={pinName}
          componentId={instance.id}
        />
      ))}
    </g>
  )
}
