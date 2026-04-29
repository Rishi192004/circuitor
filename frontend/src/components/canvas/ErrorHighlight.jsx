import React from 'react';

/**
 * ErrorHighlight component
 * 
 * Renders a solid or dashed highlight ring around a component node.
 * Includes shake animation for errors.
 */
export default function ErrorHighlight({ config }) {
  if (!config) return null;

  const isError = config.type === 'error';
  const color = config.color || 'var(--error-red)';
  const borderType = config.border === 'dashed' ? '6 3' : 'none';
  const animateClass = config.animate === 'shake' ? 'animate-shake' : '';

  return (
    <g className={`analysis-highlight ${animateClass}`}>
      {/* Outer Glow */}
      <rect
        x="-35"
        y="-35"
        width="70"
        height="70"
        rx="4"
        fill="none"
        stroke={color}
        strokeWidth="6"
        strokeOpacity="0.15"
        pointerEvents="none"
      />
      {/* Border Ring */}
      <rect
        x="-32"
        y="-32"
        width="64"
        height="64"
        rx="2"
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeDasharray={borderType}
        pointerEvents="none"
      />
      {/* Icon Badge */}
      <g transform="translate(24, -24)">
        <circle r="8" fill={color} />
        <text
          y="0.5"
          textAnchor="middle"
          dominantBaseline="middle"
          fill="white"
          style={{ fontSize: '10px', fontWeight: 'bold', fontFamily: 'sans-serif' }}
        >
          {isError ? '!' : '?'}
        </text>
      </g>
    </g>
  );
}
