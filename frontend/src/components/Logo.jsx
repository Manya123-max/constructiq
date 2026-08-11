import React from 'react'

export function Logo({ height = 36, showText = true }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', userSelect: 'none' }}>
      <svg
        width={height * 1.1}
        height={height}
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Hexagonal Outer Frame */}
        <path
          d="M60 12L102 36V84L60 108L18 84V36L60 12Z"
          stroke="#1F2937"
          strokeWidth="8"
          strokeLinejoin="round"
        />
        {/* Inner Hex Line Accent */}
        <path
          d="M60 26L88 42V78L60 94L32 78V42L60 26Z"
          stroke="#374151"
          strokeWidth="4"
          strokeLinejoin="round"
        />
        {/* Cyan Q Key / Arrow Icon */}
        <path
          d="M48 48H72V64L88 80L80 88L64 72H48V48Z"
          fill="#00E5FF"
          stroke="#00B0FF"
          strokeWidth="2"
          filter="drop-shadow(0px 0px 8px rgba(0, 229, 255, 0.6))"
        />
      </svg>
      {showText && (
        <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#111827', letterSpacing: '-0.02em' }}>
          Construct<span style={{ color: '#00E5FF' }}>IQ</span>
        </span>
      )}
    </div>
  )
}
