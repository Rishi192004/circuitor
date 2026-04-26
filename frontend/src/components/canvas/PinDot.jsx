import React from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'

export default function PinDot({ x, y, pinName, componentId }) {
  const { wireInProgress, startWire, completeWire, cancelWire } = useCircuitStore()

  function onMouseDown(e) {
    e.stopPropagation()
    if (e.button !== 0) return

    if (wireInProgress) {
      // Complete the wire
      completeWire(componentId, pinName)
    } else {
      // Start wiring from this pin
      startWire(componentId, pinName)
    }
  }

  const isSource =
    wireInProgress?.fromComponentId === componentId &&
    wireInProgress?.fromPinName === pinName

  return (
    <circle
      className="pin-dot"
      cx={x}
      cy={y}
      r={isSource ? 4.5 : 3}
      onMouseDown={onMouseDown}
      style={isSource ? { fill: 'var(--lt-selected)' } : undefined}
    >
      <title>{`${componentId}.${pinName}`}</title>
    </circle>
  )
}
