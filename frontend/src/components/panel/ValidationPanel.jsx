import React, { useState } from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'
import IssueCard from './IssueCard.jsx'
import StatusBadge from './StatusBadge.jsx'
import TopologyBanner from './TopologyBanner.jsx'

export default function ValidationPanel() {
  const {
    isValidating, validationResult, apiError, clearApiError,
    highlightedIds, setHighlightedIds, clearHighlights,
    suggestions, focusSuggestion
  } = useCircuitStore()

  const [activeIssueIdx, setActiveIssueIdx] = useState(null)

  function handleIssueClick(issue, idx) {
    setActiveIssueIdx(idx)

    // Build highlighted IDs from the issue target
    const { target, severity } = issue
    if (!target) return

    const ids = []
    if (target.type === 'component' && target.component_id) {
      ids.push({ id: target.component_id, severity })
    }
    if (target.type === 'net' && target.net_id) {
      ids.push({ id: target.net_id, severity })
    }
    if (target.type === 'multiple') {
      ;(target.component_ids ?? []).forEach(id => ids.push({ id, severity }))
      ;(target.net_ids ?? []).forEach(id => ids.push({ id, severity }))
    }
    setHighlightedIds(ids)

    // Focus matching suggestion if any
    if (issue.target && issue.suggested_fix) {
      const match = suggestions.find(s => 
        s.action === issue.suggested_fix.action && 
        (issue.target.type === 'global' || s.attach_to === `${issue.target.component_id}.${issue.target.pin_name}`)
      )
      if (match) {
        focusSuggestion(match.id)
      }
    }
  }

  const issues = validationResult?.issues ?? []
  const showTopologyBanner =
    validationResult?.phase_reached === 'TOPOLOGY' && issues.some(i => i.severity === 'error')

  return (
    <aside className="panel">
      <div className="panel__header">
        <span>Validation</span>
        {validationResult && <StatusBadge status={validationResult.status} />}
      </div>

      {/* Early-stop banner */}
      {showTopologyBanner && <TopologyBanner />}

      {/* API error */}
      {apiError && (
        <div className="api-error" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>⚠ Backend unreachable: {apiError}</span>
          <button onClick={clearApiError} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '16px' }}>&times;</button>
        </div>
      )}

      {/* Summary row */}
      {validationResult && (
        <div className="panel__summary">
          <span className="text-muted" style={{ fontSize: 11 }}>
            {validationResult.issues_count} issue{validationResult.issues_count !== 1 ? 's' : ''} ·{' '}
            phase: <span className="mono" style={{ color: 'var(--lt-blue)' }}>
              {validationResult.phase_reached}
            </span>
          </span>
          {highlightedIds.length > 0 && (
            <button
              className="btn btn--ghost"
              style={{ padding: '2px 8px', fontSize: 10 }}
              onClick={clearHighlights}
            >
              Clear highlight
            </button>
          )}
        </div>
      )}

      {/* Issue cards */}
      <div className="panel__body">
        {isValidating && (
          <div className="panel__empty">
            <div className="spinner" style={{ width: 24, height: 24 }} />
            <div className="panel__empty-text">Checking…</div>
          </div>
        )}

        {!isValidating && !validationResult && !apiError && (
          <div className="panel__empty">
            <div className="panel__empty-icon">⚡</div>
            <div className="panel__empty-text">
              Place components, draw wires,<br />then click <strong>Validate</strong>.
            </div>
          </div>
        )}

        {!isValidating && validationResult && issues.length === 0 && (
          <div className="panel__empty">
            <div className="panel__empty-icon" style={{ fontSize: 36, opacity: 0.6 }}>✓</div>
            <div className="panel__empty-text" style={{ color: 'var(--color-success)' }}>
              All checks passed!<br />
              <span className="text-muted" style={{ fontSize: 10 }}>
                {validationResult.metadata?.rules_run} rules run · ready for simulation
              </span>
            </div>
          </div>
        )}

        {!isValidating && issues.map((issue, idx) => (
          <IssueCard
            key={`${issue.error_code}-${idx}`}
            issue={issue}
            isActive={activeIssueIdx === idx}
            onClick={() => handleIssueClick(issue, idx)}
          />
        ))}
      </div>

      {/* Metadata footer */}
      {validationResult?.metadata && (
        <div className="panel__meta">
          <span>{validationResult.metadata.components_count} components · {validationResult.metadata.nets_count ?? '?'} nets</span>
          <span>{validationResult.metadata.rules_run} rules run</span>
          {validationResult.metadata.timestamp && (
            <span>{new Date(validationResult.metadata.timestamp).toLocaleTimeString()}</span>
          )}
        </div>
      )}
    </aside>
  )
}
