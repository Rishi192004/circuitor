import React from 'react'

export default function StatusBadge({ status }) {
  const map = {
    success: { label: 'PASS',    cls: 'status-badge--success', icon: '✓' },
    error:   { label: 'ERRORS',  cls: 'status-badge--error',   icon: '✕' },
    warning: { label: 'WARNINGS',cls: 'status-badge--warning', icon: '⚠' },
  }
  const cfg = map[status] ?? map.error
  return (
    <span className={`status-badge ${cfg.cls}`}>
      {cfg.icon} {cfg.label}
    </span>
  )
}
