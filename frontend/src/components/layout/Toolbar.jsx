import React, { useEffect } from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'
import StatusBadge from '../panel/StatusBadge.jsx'

export default function Toolbar() {
  const {
    instances, nets,
    isValidating, validationResult, apiError,
    runValidation, clearCanvas, deleteSelected, selectedId,
  } = useCircuitStore()

  // Keyboard: Del key deletes selected instance
  useEffect(() => {
    function onKey(e) {
      if ((e.key === 'Delete' || e.key === 'Backspace') && !e.target.closest('input')) {
        deleteSelected()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [deleteSelected])

  const isEmpty = instances.length === 0

  return (
    <header className="toolbar">
      <span className="toolbar__logo">⚡ Circuitor</span>
      <div className="toolbar__divider" />

      {/* Live circuit stats */}
      <span className="toolbar__circuit-id mono">
        {instances.length}C · {nets.length}N
      </span>

      <div className="toolbar__divider" />

      {/* Validate */}
      <button
        id="btn-validate"
        className="btn btn--primary"
        onClick={runValidation}
        disabled={isValidating || isEmpty}
        title="Serialize canvas → POST /run_pipeline"
      >
        {isValidating
          ? <><span className="spinner" /> Validating…</>
          : '▶  Validate'}
      </button>

      {/* Delete selected */}
      {selectedId && (
        <button
          id="btn-delete"
          className="btn btn--danger"
          onClick={deleteSelected}
          title="Delete selected component (Del)"
        >
          ✕ Delete
        </button>
      )}

      {/* Clear */}
      <button
        id="btn-clear"
        className="btn btn--ghost"
        onClick={clearCanvas}
        disabled={isEmpty}
        title="Clear canvas and localStorage"
      >
        ⟳ Clear
      </button>

      <div className="toolbar__spacer" />

      {/* Result badge */}
      {validationResult && !isValidating && (
        <StatusBadge status={validationResult.status} />
      )}
      {apiError && !isValidating && (
        <span className="text-error mono" style={{ fontSize: 11 }}>
          ⚠ {apiError}
        </span>
      )}

      <div className="toolbar__divider" />
      <span className="toolbar__hint">
        Drag components · Click pin to wire · Del to delete
      </span>
    </header>
  )
}
