import React from 'react'
import { getPinAbsolutePosition } from '../../constants/components.js'

/**
 * Renders the animated in-progress wire from a source pin to the cursor.
 * Uses orthogonal routing (horizontal first, then vertical).
 * Receives `instances` (array with new position:{x,y} shape).
 */
export default function WireInProgress({ wireInProgress, mousePos, instances }) {
  if (!wireInProgress || !mousePos) return null

  const { fromComponentId, fromPinName } = wireInProgress
  const srcInst = instances.find(i => i.id === fromComponentId)
  if (!srcInst) return null

  const from = getPinAbsolutePosition(srcInst, fromPinName)
  const to   = mousePos

  // L-shape: go horizontal to target X, then vertical to target Y
  const d = `M ${from.x} ${from.y} L ${to.x} ${from.y} L ${to.x} ${to.y}`

  return (
    <path
      className="wire-in-progress"
      d={d}
      pointerEvents="none"
    />
  )
}
