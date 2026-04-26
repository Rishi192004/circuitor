import React, { useRef, useState, useCallback, useEffect } from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'
import ComponentNode from './ComponentNode.jsx'
import WireLayer from './WireLayer.jsx'
import WireInProgress from './WireInProgress.jsx'
import GhostNode from './GhostNode.jsx'

const GRID = 20

export default function CircuitCanvas() {
  const svgRef   = useRef(null)
  const [mousePos, setMousePos] = useState(null)

  const {
    instances, addInstance,
    wireInProgress, cancelWire, clearSelection,
    suggestions, acceptSuggestion, cycleFocus
  } = useCircuitStore()

  // ── Convert DOM coords → SVG canvas coords ─────────────────
  function toSVGPoint(clientX, clientY) {
    const svg = svgRef.current
    if (!svg) return null
    const pt  = svg.createSVGPoint()
    pt.x = clientX; pt.y = clientY
    return pt.matrixTransform(svg.getScreenCTM().inverse())
  }

  // ── Drag-and-drop from sidebar ──────────────────────────────
  function onDragOver(e) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }

  function onDrop(e) {
    e.preventDefault()
    const type = e.dataTransfer.getData('componentType')
    if (!type) return
    const pt = toSVGPoint(e.clientX, e.clientY)
    if (!pt) return
    addInstance(type, pt.x, pt.y)   // ← addInstance (was addComponent)
  }

  // ── Mouse move: track cursor for live wire preview ──────────
  const onMouseMove = useCallback((e) => {
    if (!wireInProgress) { setMousePos(null); return }
    const pt = toSVGPoint(e.clientX, e.clientY)
    if (pt) setMousePos({ x: pt.x, y: pt.y })
  }, [wireInProgress])

  // ── Background click: deselect or cancel wiring ─────────────
  function onSVGClick(e) {
    const isBackground =
      e.target === svgRef.current ||
      e.target.classList.contains('grid-rect')
    if (!isBackground) return
    if (wireInProgress) {
      cancelWire()
    } else {
      clearSelection()
    }
  }

  // ── Global Tab Key Listener for Ghost Suggestions ───────────
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Tab' && suggestions.length > 0) {
        e.preventDefault()
        const focused = suggestions.find(s => s.focused)
        if (focused) {
          acceptSuggestion(focused.id)
        } else {
          cycleFocus()
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [suggestions, acceptSuggestion, cycleFocus])

  return (
    <div
      className="canvas-area"
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      <svg
        ref={svgRef}
        id="circuit-canvas"
        className={`canvas-svg${wireInProgress ? ' wiring' : ''}`}
        onMouseMove={onMouseMove}
        onClick={onSVGClick}
        onContextMenu={e => { e.preventDefault(); cancelWire() }}
      >
        <defs>
          <pattern
            id="ltspice-grid"
            x="0" y="0"
            width={GRID} height={GRID}
            patternUnits="userSpaceOnUse"
          >
            <circle cx={GRID / 2} cy={GRID / 2} r="0.7" fill="var(--grid-dot)" />
          </pattern>
        </defs>

        {/* Dot-grid background */}
        <rect
          className="grid-rect"
          x="-5000" y="-5000"
          width="10000" height="10000"
          fill="url(#ltspice-grid)"
        />

        {/* Wires — rendered below components */}
        <WireLayer />

        {/* In-progress wire */}
        <WireInProgress
          wireInProgress={wireInProgress}
          mousePos={mousePos}
          instances={instances}           // ← instances (was components)
        />

        {/* Placed instances */}
        {instances.map(inst => (
          <ComponentNode
            key={inst.id}
            instance={inst}               // ← instance prop (was component)
            svgRef={svgRef}
          />
        ))}

        {/* Ghost suggestions layer */}
        <g id="ghost-layer">
          {suggestions.map(s => (
            <GhostNode key={s.id} suggestion={s} />
          ))}
        </g>
      </svg>

      {/* Empty-state hint */}
      {instances.length === 0 && (
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexDirection: 'column', gap: 10,
        }}>
          <div style={{ fontSize: 36, opacity: 0.12 }}>⚡</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', opacity: 0.5 }}>
            Drag components from the sidebar to get started
          </div>
        </div>
      )}
    </div>
  )
}
