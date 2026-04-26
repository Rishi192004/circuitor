import React from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'
import { getPinAbsolutePosition } from '../../constants/components.js'

/**
 * Renders all committed nets as orthogonal L-shaped SVG paths.
 * Net pins are stored as "ComponentId.pinName" strings and parsed here.
 */
export default function WireLayer() {
  const { instances, nets, highlightedIds } = useCircuitStore()

  // Fast instance lookup by id
  const instMap = Object.fromEntries(instances.map(i => [i.id, i]))

  return (
    <g id="wire-layer">
      {nets.map(net => {
        // Need at least 2 endpoints to draw a wire
        if (!net.pins || net.pins.length < 2) return null

        const [pin0, pin1] = net.pins

        // Parse "ComponentId.pinName" strings
        const dot0 = pin0.indexOf('.')
        const dot1 = pin1.indexOf('.')
        if (dot0 === -1 || dot1 === -1) return null

        const compId0  = pin0.slice(0, dot0)
        const pinName0 = pin0.slice(dot0 + 1)
        const compId1  = pin1.slice(0, dot1)
        const pinName1 = pin1.slice(dot1 + 1)

        const inst0 = instMap[compId0]
        const inst1 = instMap[compId1]
        if (!inst0 || !inst1) return null

        const pos0 = getPinAbsolutePosition(inst0, pinName0)
        const pos1 = getPinAbsolutePosition(inst1, pinName1)

        // Orthogonal routing: horizontal from pos0, then vertical to pos1
        const d = `M ${pos0.x} ${pos0.y} L ${pos1.x} ${pos0.y} L ${pos1.x} ${pos1.y}`

        // Highlight class from panel issue click
        const highlight = highlightedIds.find(h => h.id === net.id)
        let extraClass = ''
        if (highlight?.severity === 'error')   extraClass = ' highlighted-error'
        if (highlight?.severity === 'warning') extraClass = ' highlighted-warning'

        return (
          <path
            key={net.id}
            id={`wire-${net.id}`}
            className={`wire-path${extraClass}`}
            d={d}
          />
        )
      })}
    </g>
  )
}
