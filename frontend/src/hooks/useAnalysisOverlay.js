import { useMemo } from 'react';

/**
 * useAnalysisOverlay hook
 * 
 * Maps a backend AnalysisResult into a per-component-ID overlay configuration.
 * Groups errors and warnings for high-performance canvas rendering.
 */
export function useAnalysisOverlay(analysisResult) {
  return useMemo(() => {
    if (!analysisResult) return {};

    const overlayMap = {};

    // 1. Process Errors (Strict red, solid, shake)
    if (analysisResult.errors) {
      analysisResult.errors.forEach(error => {
        const target = error.target;
        if (target.type === 'component') {
          overlayMap[target.component_id] = {
            type: 'error',
            color: 'var(--error-red)',
            border: 'solid',
            icon: 'error',
            animate: 'shake',
            message: error.userExplanation
          };
        } else if (target.type === 'multiple' && target.component_ids) {
          target.component_ids.forEach(id => {
            overlayMap[id] = {
              type: 'error',
              color: 'var(--error-red)',
              border: 'solid',
              icon: 'error',
              animate: 'shake',
              message: error.userExplanation
            };
          });
        }
      });
    }

    // 2. Process Warnings (Orange, dashed, static)
    if (analysisResult.warnings) {
      analysisResult.warnings.forEach(warning => {
        const target = warning.target;
        const addWarning = (id) => {
          // Errors take priority over warnings visually
          if (overlayMap[id]?.type === 'error') return;
          overlayMap[id] = {
            type: 'warning',
            color: 'var(--warning-orange)',
            border: 'dashed',
            icon: 'warning',
            animate: 'none',
            message: warning.userExplanation
          };
        };

        if (target.type === 'component') {
          addWarning(target.component_id);
        } else if (target.type === 'multiple' && target.component_ids) {
          target.component_ids.forEach(id => addWarning(id));
        }
      });
    }

    return overlayMap;
  }, [analysisResult]);
}
