import React from 'react';
import { useCircuitStore } from '../../store/circuitStore.js';
import IssueCard from '../panel/IssueCard.jsx';
import StatusBadge from '../panel/StatusBadge.jsx';

/**
 * AnalysisSidebar
 * 
 * Replaces the old ValidationPanel. 
 * Strictly separates "Issues" (Errors/Warnings) from "Suggestions" (Ghosts).
 */
export default function AnalysisSidebar() {
  const {
    isValidating, validationResult, suggestions, focusSuggestion
  } = useCircuitStore();

  const [hintsExpanded, setHintsExpanded] = React.useState(false);

  const errors = validationResult?.errors || [];
  const warnings = validationResult?.warnings || [];
  const hints = validationResult?.hints || [];
  const allIssues = [...errors, ...warnings];

  return (
    <aside className="panel analysis-sidebar">
      <div className="panel__header">
        <span>Analysis</span>
        {validationResult && <StatusBadge status={validationResult.isSimulationReady ? 'ok' : 'error'} />}
      </div>

      <div className="panel__body">
        {isValidating && (
          <div className="panel__empty">
            <div className="spinner" />
            <div className="panel__empty-text">Analyzing Circuit...</div>
          </div>
        )}

        {!isValidating && (
          <>
            {/* 1. ISSUES SECTION (Errors & Warnings) */}
            <section className="analysis-section analysis-section--issues">
              <div className="analysis-section__header">
                <span>Issues</span>
                <span className="analysis-section__count">{allIssues.length}</span>
              </div>
              
              {allIssues.length === 0 ? (
                <div className="panel__empty" style={{ minHeight: '60px' }}>
                  <div className="panel__empty-text" style={{ fontSize: '11px' }}>No issues detected.</div>
                </div>
              ) : (
                allIssues.map((issue, idx) => (
                  <IssueCard 
                    key={`issue-${idx}`} 
                    issue={issue} 
                    // Map ValidationResult back to the legacy IssueCard expectations if needed
                    // But we'll assume IssueCard is updated or handles it.
                  />
                ))
              )}
            </section>

            <div className="toolbar__divider" style={{ width: '100%', height: '1px', margin: '8px 0' }} />

            {/* 2. SUGGESTIONS SECTION (Ghost Components) */}
            <section className="analysis-section analysis-section--suggestions">
              <div className="analysis-section__header">
                <span>Suggestions</span>
                <span className="analysis-section__count">{suggestions.length}</span>
              </div>

              {suggestions.length === 0 ? (
                <div className="panel__empty" style={{ minHeight: '60px' }}>
                  <div className="panel__empty-text" style={{ fontSize: '11px' }}>No suggestions available.</div>
                </div>
              ) : (
                suggestions.map((s, idx) => (
                  <div 
                    key={s.id}
                    className={`issue-card ghost-card ${s.focused ? 'active' : ''}`}
                    onClick={() => focusSuggestion(s.id)}
                  >
                    <div className="issue-card__rule" style={{ color: 'var(--suggestion-purple)' }}>
                      Suggest: Add {s.component_type}
                    </div>
                    <div className="issue-card__explanation">
                      {s.reason || "Improve circuit design by adding this component."}
                    </div>
                    <div className="issue-card__fix">
                      <span style={{ fontSize: '10px' }}>Click to place or press Tab</span>
                    </div>
                  </div>
                ))
              )}
            </section>

            <div className="toolbar__divider" style={{ width: '100%', height: '1px', margin: '8px 0' }} />

            {/* 3. SIMULATION NOTES SECTION (Informational Hints) */}
            <section className="analysis-section analysis-section--hints">
              <div 
                className="analysis-section__header" 
                style={{ cursor: 'pointer' }}
                onClick={() => setHintsExpanded(!hintsExpanded)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '10px' }}>{hintsExpanded ? '▼' : '▶'}</span>
                  <span>Simulation Notes</span>
                </div>
                <span className="analysis-section__count">{hints.length}</span>
              </div>

              {hintsExpanded && (
                <div className="analysis-section__content" style={{ padding: '0 8px 8px' }}>
                  {hints.length === 0 ? (
                    <div className="panel__empty" style={{ minHeight: '40px' }}>
                      <div className="panel__empty-text" style={{ fontSize: '10px' }}>No notes for this circuit.</div>
                    </div>
                  ) : (
                    hints.map((hint, idx) => (
                      <div 
                        key={`hint-${idx}`}
                        className="issue-card hint-card"
                      >
                        <div className="issue-card__rule" style={{ fontSize: '10px' }}>
                          ℹ {hint.hintId}
                        </div>
                        <div className="issue-card__explanation" style={{ fontSize: '10px', marginBottom: 0 }}>
                          {hint.message}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </div>

      {/* Footer Info */}
      {validationResult && (
        <div className="panel__meta">
          <span>Simulation: {validationResult.isSimulationReady ? 'READY' : 'BLOCKED'}</span>
          <span>{errors.length} Errors · {warnings.length} Warnings</span>
        </div>
      )}
    </aside>
  );
}
