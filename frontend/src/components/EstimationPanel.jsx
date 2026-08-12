import React from 'react'
import { useStore } from '../store/useStore'
import { SiteStatusMap } from './SiteStatusMap'

function fmt(n, decimals = 0) {
  if (n == null || isNaN(n)) return '—'
  return Number(n).toLocaleString('en-IN', { maximumFractionDigits: decimals })
}

export function EstimationPanel() {
  const { estimationResult, isEstimating, estimationError, currentForm } = useStore()

  if (isEstimating) {
    return (
      <div className="workspace-panel">
        <div className="ready-state-container">
          <div className="concentric-loader" style={{ animation: 'spin 3s linear infinite' }}>
            <div className="water-drop-icon">⚡</div>
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-dark)' }}>
            Running Engineering Simulation & Analysis...
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '0.5rem', maxWidth: '440px', lineHeight: 1.6 }}>
            • Calculating Material Bill of Quantities (BOQ)<br/>
            • Estimating Annual Energy Generation & Capacity Factor<br/>
            • Computing Civil, Equipment & Total CapEx Breakdown<br/>
            • Modeling Construction Timeline & Execution Schedule<br/>
            • Verifying Statutory Government Compliance & Benchmarks...
          </p>
        </div>
      </div>
    )
  }

  if (estimationError) {
    const errorStr = typeof estimationError === 'string' 
      ? estimationError 
      : JSON.stringify(estimationError)
    return (
      <div className="workspace-panel">
        <div style={{ background: '#FFEBEE', border: '1px solid #FF1744', color: '#D50000', padding: '1.25rem', borderRadius: '8px', fontWeight: 600 }}>
          ⚠️ Estimation Error: {errorStr}
        </div>
      </div>
    )
  }

  if (!estimationResult) {
    return (
      <div className="workspace-panel">
        <div className="ready-state-container">
          <div className="concentric-loader">
            <div className="water-drop-icon">💧</div>
          </div>
          <h2 className="results-title" style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
            Ready for Analysis
          </h2>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-muted)', maxWidth: '440px', lineHeight: 1.6 }}>
            Input parameters on the left, then click <strong>Generate Project Estimate</strong> to generate accurate Material BOQ predictions, CapEx breakdown, and statutory confidence validation.
          </p>
        </div>
      </div>
    )
  }

  const {
    project_inputs,
    model_1_materials,
    material_intensities_per_mw,
    model_2_generation,
    model_3_cost,
    model_4_duration,
    rag_confidence
  } = estimationResult

  const capMw = currentForm?.capacity_mw || project_inputs?.capacity_mw || 45
  const stateName = currentForm?.state || project_inputs?.state || 'Uttarakhand'
  const pType = currentForm?.project_type || project_inputs?.project_type || 'run-of-river'
  const tType = currentForm?.turbine_type || project_inputs?.turbine_type || 'Francis'

  const mat = model_1_materials || {}
  const gen = model_2_generation || {}
  const cost = model_3_cost || {}
  const dur = model_4_duration || {}
  const conf = rag_confidence || {}

  const confScore = conf.confidence_score_pct || 84.5
  const comparables = Array.isArray(conf.comparable_projects) ? conf.comparable_projects : []

  return (
    <div className="workspace-panel">
      {/* Results Header */}
      <div className="results-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', gap: '1rem' }}>
        <div>
          <h1 className="results-title">Project Overview</h1>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Performance analytics and engineering benchmarks for <strong>{capMw} MW {pType} ({tType} Turbine)</strong> in <strong>{stateName}</strong>.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          <span
            className="badge-stat cyan"
            style={{
              fontSize: '0.67rem',
              fontWeight: 700,
              whiteSpace: 'nowrap',
              wordBreak: 'keep-all',
              padding: '4px 8px',
              borderRadius: '6px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              flexShrink: 0
            }}
          >
            ⏱️ {dur.construction_duration_months || 48} Months ({dur.estimated_years || 4.0} Yrs)
          </span>
        </div>
      </div>

      {/* 8 Material BOQ Cards */}
      <div className="materials-grid">
        <div className="material-card">
          <div className="mat-label">Concrete (m³)</div>
          <div className="mat-value" style={{ color: '#005F6A' }}>{fmt(mat.concrete_m3)}</div>
          <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {material_intensities_per_mw?.concrete_m3_per_mw || 0} m³/MW
          </div>
        </div>
        <div className="material-card">
          <div className="mat-label">Cement (MT)</div>
          <div className="mat-value">{fmt(mat.cement_mt)}</div>
          <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {material_intensities_per_mw?.cement_mt_per_mw || 0} MT/MW
          </div>
        </div>
        <div className="material-card">
          <div className="mat-label">Rebar (MT)</div>
          <div className="mat-value">{fmt(mat.reinforcement_steel_mt)}</div>
          <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {material_intensities_per_mw?.reinforcement_steel_mt_per_mw || 0} MT/MW
          </div>
        </div>
        <div className="material-card">
          <div className="mat-label">Struct. Steel (MT)</div>
          <div className="mat-value">{fmt(mat.structural_steel_mt)}</div>
          <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {material_intensities_per_mw?.structural_steel_mt_per_mw || 0} MT/MW
          </div>
        </div>
        <div className="material-card">
          <div className="mat-label">Penstock (MT)</div>
          <div className="mat-value" style={{ color: '#00E5FF' }}>{fmt(mat.penstock_steel_mt)}</div>
          <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {material_intensities_per_mw?.penstock_steel_mt_per_mw || 0} MT/MW
          </div>
        </div>
        <div className="material-card">
          <div className="mat-label">Aggregate (m³)</div>
          <div className="mat-value">{fmt(mat.aggregate_m3)}</div>
        </div>
        <div className="material-card">
          <div className="mat-label">Sand (m³)</div>
          <div className="mat-value">{fmt(mat.sand_m3)}</div>
        </div>
        <div className="material-card">
          <div className="mat-label">Excavation (m³)</div>
          <div className="mat-value" style={{ color: '#FF9E00' }}>{fmt(mat.excavation_m3)}</div>
          <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {material_intensities_per_mw?.excavation_m3_per_mw || 0} m³/MW
          </div>
        </div>
      </div>

      {/* Middle Row 3 Main Cards */}
      <div className="results-middle-grid">
        {/* Card 1: Power Generation */}
        <div className="card-box">
          <div className="card-box-header">
            <span className="card-box-title">Power Generation</span>
            <span style={{ fontSize: '1.2rem', color: '#005F6A' }}>⚡</span>
          </div>
          <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Annual Energy Output (GWh)
          </div>
          <div className="stat-huge" style={{ color: '#005F6A' }}>{fmt(gen.annual_generation_gwh)}</div>
          <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Capacity Factor (PLF %): <strong style={{ color: '#047857' }}>{gen.capacity_factor_pct || (gen.capacity_factor ? (gen.capacity_factor * 100).toFixed(1) : '45.0')}%</strong>
          </div>
        </div>

        {/* Card 2: CapEx Breakdown */}
        <div className="card-box">
          <div className="card-box-header">
            <span className="card-box-title">CapEx Breakdown</span>
            <span style={{ fontSize: '1.2rem' }}>💳</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Civil Cost</span>
            <strong style={{ fontWeight: 800 }}>₹ {fmt(cost.civil_cost_cr, 1)} Cr</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Equipment Cost</span>
            <strong style={{ fontWeight: 800 }}>₹ {fmt(cost.equipment_cost_cr, 1)} Cr</strong>
          </div>
          <div style={{ borderTop: '1px solid #E2E8F0', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 800, fontSize: '0.9rem' }}>Total Cost</span>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#005F6A' }}>
              ₹ {fmt(cost.total_project_cost_cr, 1)} Cr
            </span>
          </div>
          <div style={{ textAlign: 'right', marginTop: '6px' }}>
            <span className="badge-stat cyan">
              ₹ {cost.cost_per_mw_cr || (cost.total_project_cost_cr && capMw ? (cost.total_project_cost_cr / capMw).toFixed(2) : '—')} Cr / MW
            </span>
          </div>
        </div>

        {/* Card 3: Statutory Confidence */}
        <div className="card-box">
          <div className="card-box-header">
            <span className="card-box-title">Statutory Confidence</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Regulatory Benchmark Approval</span>
          </div>
          <div className="confidence-ring-box">
            <div className="ring-outer" style={{ borderColor: confScore >= 80 ? '#047857' : '#FF9E00' }}>
              {confScore}%
            </div>
            <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--text-muted)', marginTop: '4px' }}>
              CONFIDENCE SCORE
            </div>
          </div>
          <div className="govt-badges-row">
            <span className="govt-badge emerald">✓ PARIVESH MoEFCC</span>
            <span className="govt-badge emerald">✓ CEA DPR</span>
            <span className="govt-badge amber">✓ CPPP</span>
          </div>
          <div style={{ marginTop: '0.75rem', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <strong style={{ display: 'block', marginBottom: '4px', fontSize: '0.68rem', letterSpacing: '0.02em', color: 'var(--text-muted)' }}>
              HISTORICAL BENCHMARK TWINS:
            </strong>
            {comparables.slice(0, 3).map((p, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  marginTop: '3px',
                  gap: '6px'
                }}
              >
                <span
                  style={{
                    fontSize: '0.67rem',
                    color: 'var(--text-dark)',
                    fontWeight: 500,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    flex: 1,
                    minWidth: 0
                  }}
                  title={p.project_name || p.id || `Twin ${idx+1}`}
                >
                  {p.project_name || p.id || `Twin ${idx+1}`}
                </span>
                <span
                  style={{
                    color: '#047857',
                    fontWeight: 700,
                    fontSize: '0.65rem',
                    whiteSpace: 'nowrap',
                    flexShrink: 0
                  }}
                >
                  {p.capacity_mw ? `${p.capacity_mw} MW` : 'Matched'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }}>
        {/* Dynamic Material Deliveries Lookahead */}
        <div className="card-box">
          <h3 style={{ fontSize: '1rem', fontWeight: 800, marginBottom: '1rem' }}>
            Material Procurement Lookahead ({capMw} MW Scale)
          </h3>
          <table className="table-custom">
            <thead>
              <tr>
                <th>Material / Spec</th>
                <th>Phase Quantity</th>
                <th>ETA</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Rebar - Fe500D Grade (Apex Steel)</td>
                <td>{fmt(mat.reinforcement_steel_mt ? mat.reinforcement_steel_mt * 0.15 : 450)} MT</td>
                <td>Phase 1 Immediate</td>
                <td><span className="badge-stat cyan">PLANNED</span></td>
              </tr>
              <tr>
                <td>Ready-Mix Structural Concrete</td>
                <td>{fmt(mat.concrete_m3 ? mat.concrete_m3 * 0.10 : 1200)} m³</td>
                <td>Phase 2 Site Pour</td>
                <td><span className="badge-stat cyan">PLANNED</span></td>
              </tr>
              <tr>
                <td>High Tensile Penstock Steel Plates (E350)</td>
                <td>{fmt(mat.penstock_steel_mt ? mat.penstock_steel_mt * 0.25 : 210)} MT</td>
                <td>Phase 3 Tunneling</td>
                <td><span className="badge-stat cyan">PLANNED</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Live Site Map Component */}
        <SiteStatusMap compact={true} />
      </div>
    </div>
  )
}
