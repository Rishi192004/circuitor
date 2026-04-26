import React from 'react'

export default function TopologyBanner() {
  return (
    <div className="topology-banner">
      <span className="topology-banner__icon">⚠</span>
      <div className="topology-banner__text">
        <strong>Validation stopped early.</strong> Fatal wiring errors found in the
        TOPOLOGY phase — PHYSICS checks were skipped.
        Fix floating pins / empty nets first, then re-validate.
      </div>
    </div>
  )
}
