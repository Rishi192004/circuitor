import React, { useState } from 'react'
import { useCircuitStore } from '../../store/circuitStore.js'

const SEVERITY_ICON = { error: '✕', warning: '⚠' }
const ACTION_LABEL = {
  wire_pin:         '→ Flash unconnected pin',
  delete_or_connect:'→ Highlight dangling wire',
  add_ground:       '→ Add Ground component',
  add_source:       '→ Add Voltage Source',
  break_short:      '→ Insert resistor to break short',
  separate_outputs: '→ Separate output pins',
  edit_property:    '→ Edit component value',
  break_loop:       '→ Break voltage loop',
}

export default function IssueCard({ issue, isActive, onClick }) {
  const { suggestions } = useCircuitStore()
  const { severity, error_code, rule_name, user_explanation, technical_message, suggested_fix, target } = issue

  const matchingSuggestion = suggestions.find(s => 
    s.action === suggested_fix?.action && 
    (target?.type === 'global' || s.attach_to === `${target?.component_id}.${target?.pin_name}`)
  )

  const actionLabel = suggested_fix?.action
    ? (ACTION_LABEL[suggested_fix.action] ?? `→ ${suggested_fix.description ?? suggested_fix.action}`)
    : null

  return (
    <div
      id={`issue-${error_code}`}
      className={`issue-card issue-card--${severity}${isActive ? ' active' : ''}`}
      onClick={onClick}
      title="Click to highlight on canvas"
    >
      <div className="issue-card__header">
        <span className={`issue-card__severity issue-card__severity--${severity}`}>
          {SEVERITY_ICON[severity]} {severity}
        </span>
        <span className="issue-card__code">{error_code}</span>
        {matchingSuggestion && (
          <span className="issue-card__ghost-badge" style={{ marginLeft: 8, fontSize: 10, background: 'rgba(79, 195, 247, 0.1)', color: 'var(--lt-blue)', padding: '2px 6px', borderRadius: 4 }}>
            👻 Shown on canvas
          </span>
        )}
        {target?.type && (
          <span className="issue-card__code" style={{ marginLeft: 'auto', color: 'var(--lt-blue)' }}>
            {target.type === 'component' && target.component_id}
            {target.type === 'net'       && target.net_id}
            {target.type === 'global'    && 'global'}
          </span>
        )}
      </div>

      <div className="issue-card__rule">{rule_name}</div>
      <div className="issue-card__explanation">{user_explanation}</div>

      {actionLabel && (
        <div className="issue-card__fix">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          {actionLabel}
        </div>
      )}
    </div>
  )
}
