import React from 'react'
import { COMPONENT_LIBRARY } from '../../constants/components.js'

function formatLabel(key) {
  return key.replaceAll('_', ' ')
}

export default function ComponentPropertiesEditor({
  instance,
  onChange,
  onClose,
  compact = false,
}) {
  if (!instance) return null

  const lib = COMPONENT_LIBRARY[instance.type]
  const defaultProps = lib?.defaultProps ?? {}
  const valueProps = instance.properties ?? {}
  const keys = Array.from(new Set([...Object.keys(defaultProps), ...Object.keys(valueProps)]))

  return (
    <div className={compact ? 'prop-editor prop-editor--compact' : 'prop-editor'}>
      <div className="prop-editor__header">
        <div>
          <div className="prop-editor__title">{lib?.label ?? instance.type}</div>
          <div className="prop-editor__subtitle mono">{instance.id}</div>
        </div>
        {onClose && (
          <button
            className="prop-editor__close"
            onClick={onClose}
            aria-label="Close properties editor"
            title="Close"
            type="button"
          >
            ×
          </button>
        )}
      </div>

      <div className="prop-editor__fields">
        {keys.length === 0 && (
          <div className="prop-editor__empty text-muted">No editable properties.</div>
        )}
        {keys.map(key => (
          <label key={key} className="prop-editor__field">
            <span className="prop-editor__label mono">{formatLabel(key)}</span>
            <input
              type="text"
              value={valueProps[key] ?? ''}
              onChange={e => onChange?.(key, e.target.value)}
              placeholder={defaultProps[key] ?? ''}
            />
          </label>
        ))}
      </div>
    </div>
  )
}
