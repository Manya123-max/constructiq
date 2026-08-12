import React, { useState, useEffect } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { SiteStatusMap } from './SiteStatusMap'

const TABS = [
  { id: 'status', label: 'Project Status' },
  { id: 'delays', label: 'Delay Detector' },
  { id: 'rootcause', label: 'Root Cause Analysis' },
  { id: 'materials', label: 'Material Availability' },
  { id: 'procurement', label: 'Procurement Risk' },
]

export function MonitoringDashboard() {
  const { estimationResult, projects } = useStore()
  const [selectedProjectId, setSelectedProjectId] = useState('HP-001')
  const [activeTab, setActiveTab] = useState('status')
  const [data, setData] = useState(null)
  const [projectMeta, setProjectMeta] = useState(null)
  const [allProjectsList, setAllProjectsList] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Fetch full project list from backend on mount or when estimation changes
  useEffect(() => {
    api.getProjects(400)
      .then((res) => {
        if (res?.data) setAllProjectsList(res.data)
      })
      .catch(() => {})
  }, [estimationResult])

  // Sync latest estimated project ID if available
  useEffect(() => {
    if (estimationResult?.project_id) {
      setSelectedProjectId(estimationResult.project_id)
    }
  }, [estimationResult])

  // Fetch project metadata (name, cost, capacity) per selected project for dynamic CapEx card / Planning Phase
  useEffect(() => {
    api.getProject(selectedProjectId)
      .then((res) => setProjectMeta(res.data))
      .catch(() => setProjectMeta(null))
  }, [selectedProjectId])

  useEffect(() => {
    const isNew = String(selectedProjectId).startsWith('HP-EST-') || (estimationResult?.project_id && selectedProjectId === estimationResult.project_id)
    if (isNew) {
      setLoading(false)
      setError(null)
      setData(null)
      return
    }

    setLoading(true)
    setError(null)

    let fetcher
    if (activeTab === 'status') fetcher = api.monitorStatus(selectedProjectId)
    else if (activeTab === 'delays') fetcher = api.monitorDelays(selectedProjectId)
    else if (activeTab === 'rootcause') fetcher = api.monitorRootcause(selectedProjectId)
    else if (activeTab === 'materials') fetcher = api.monitorMaterials(selectedProjectId)
    else if (activeTab === 'procurement') fetcher = api.monitorProcurement(selectedProjectId)

    fetcher
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message || 'Failed to fetch agent monitoring telemetry.'))
      .finally(() => setLoading(false))
  }, [activeTab, selectedProjectId, estimationResult])

  // Detect if the selected project is a freshly estimated AI project (starts with HP-EST- or matches in-memory result)
  const isNewEstimate = String(selectedProjectId).startsWith('HP-EST-') || (estimationResult?.project_id && selectedProjectId === estimationResult.project_id)

  const plannedPct = isNewEstimate ? 0.0 : (data?.planned_pct ?? 70.0)
  const actualPct = isNewEstimate ? 0.0 : (data?.actual_pct ?? 68.4)
  const variancePct = isNewEstimate ? 0.0 : (data?.variance ?? (plannedPct - actualPct))
  const healthStatus = isNewEstimate ? 'Not Started' : (data?.status || (variancePct > 5 ? 'Critical Delay' : variancePct > 2 ? 'Minor Delay' : 'On Track'))

  // Extract display values for the Planning Phase view
  const isCurrentStoreResult = estimationResult?.project_id === selectedProjectId
  const estCapMw = isCurrentStoreResult
    ? estimationResult?.model_1_turbine?.recommended_capacity_mw
    : (projectMeta?.capacity_mw || projectMeta?.hydro_features?.capacity_mw)

  const capexCr = isCurrentStoreResult
    ? estimationResult?.model_3_cost?.total_project_cost_cr
    : (projectMeta?.project_cost_cr || projectMeta?.real_cost_cr || null)

  const estGenGwh = isCurrentStoreResult
    ? estimationResult?.model_2_generation?.annual_generation_gwh
    : (projectMeta?.annual_generation_gwh || null)

  const estProjTitle = isCurrentStoreResult
    ? `${estimationResult.project_id} (Latest Simulation)`
    : (projectMeta?.project_name || selectedProjectId)

  // Dynamic risk bar proportions based on real delayed vs on-track counts from backend
  const delayedCount = isNewEstimate ? 0 : (data?.delayed_count ?? 3)
  const onTrackCount = isNewEstimate ? 0 : (data?.on_track_count ?? 3)
  const totalActivities = isNewEstimate ? 0 : (data?.total_activities ?? (delayedCount + onTrackCount) || 6)
  const redFlex = isNewEstimate ? 0 : Math.max(1, delayedCount)
  const greenFlex = isNewEstimate ? 1 : Math.max(1, onTrackCount)
  const amberFlex = isNewEstimate ? 0 : Math.max(1, totalActivities - delayedCount - onTrackCount)

  // Helper to format material quantities
  const formatMaterialQty = (val, unit) => {
    if (val == null) return `— ${unit}`
    return `${Number(val).toLocaleString('en-IN', { maximumFractionDigits: 0 })} ${unit}`
  }

  // Calculate material requirements (read from estimationResult store or proportional to MW capacity)
  const concreteVal = isCurrentStoreResult 
    ? estimationResult?.model_1_materials?.concrete_m3
    : (projectMeta?.capacity_mw ? projectMeta.capacity_mw * 1500 : 350000)
  const cementVal = isCurrentStoreResult
    ? estimationResult?.model_1_materials?.cement_mt
    : (projectMeta?.capacity_mw ? projectMeta.capacity_mw * 350 : 80000)
  const rebarVal = isCurrentStoreResult
    ? estimationResult?.model_1_materials?.rebar_steel_mt
    : (projectMeta?.capacity_mw ? projectMeta.capacity_mw * 80 : 25000)
  const penstockVal = isCurrentStoreResult
    ? estimationResult?.model_1_materials?.penstock_steel_mt
    : (projectMeta?.capacity_mw ? projectMeta.capacity_mw * 15 : 5000)

  // Overrides for activities, delays, contributing factors, materials, and procurement risks
  const activities = isNewEstimate ? [
    { name: 'Site Excavation & Foundation', planned_pct: 0, actual_pct: 0, variance: 0, status: 'Not Started' },
    { name: 'Dam & Concrete Works', planned_pct: 0, actual_pct: 0, variance: 0, status: 'Not Started' },
    { name: 'Headrace Tunnel Excavation', planned_pct: 0, actual_pct: 0, variance: 0, status: 'Not Started' },
    { name: 'Powerhouse & E&M Erection', planned_pct: 0, actual_pct: 0, variance: 0, status: 'Not Started' },
  ] : (data?.activities || [
    { name: 'Site Excavation & Foundation', planned_pct: 100, actual_pct: 95, variance: 5, status: 'On Track' },
    { name: 'Dam Concrete Pouring', planned_pct: 65, actual_pct: 48, variance: 17, status: 'Minor Delay' },
    { name: 'Headrace Tunnel Excavation', planned_pct: 40, actual_pct: 28, variance: 12, status: 'Critical Delay' },
    { name: 'Powerhouse & E&M Erection', planned_pct: 25, actual_pct: 15, variance: 10, status: 'Minor Delay' },
  ])

  const delayedActivities = isNewEstimate ? [] : (data?.delayed_activities || [
    { name: 'Headrace Tunnel Boring Section 3', planned_pct: 40, actual_pct: 28, delay_days: 24, impact: 'Critical Path' },
    { name: 'Dam Spillway Concrete Block B', planned_pct: 65, actual_pct: 48, delay_days: 12, impact: 'Moderate' },
  ])

  const contributingFactors = isNewEstimate ? [] : (data?.contributing_factors || [
    { type: 'Geological Variation', description: 'Unexpected shear zone in tunnel face requiring additional support', impact: 'High', mitigation: 'Steel rib insertion & grouting' },
    { type: 'Monsoon Disruption', description: 'Heavy rainfall stalled civil works and access roads', impact: 'Medium', mitigation: 'Prioritize indoor powerhouse works during precipitation' },
  ])

  const materials = isNewEstimate ? [
    { material_name: 'Grade M25/M40 Structural Concrete', required: formatMaterialQty(concreteVal, 'm³'), available: formatMaterialQty(concreteVal, 'm³'), short: '0 m³', risk_level: 'Low' },
    { material_name: 'OPC 43/53 Grade Cement', required: formatMaterialQty(cementVal, 'MT'), available: formatMaterialQty(cementVal, 'MT'), short: '0 MT', risk_level: 'Low' },
    { material_name: 'Fe500D Reinforcement Rebar', required: formatMaterialQty(rebarVal, 'MT'), available: formatMaterialQty(rebarVal, 'MT'), short: '0 MT', risk_level: 'Low' },
    { material_name: 'Penstock High Tensile Steel', required: formatMaterialQty(penstockVal, 'MT'), available: formatMaterialQty(penstockVal, 'MT'), short: '0 MT', risk_level: 'Low' },
  ] : (data?.materials || [
    { material_name: 'Fe500D Reinforcement Rebar', required: '42,500 MT', available: '38,000 MT', short: '4,500 MT', risk_level: 'High' },
    { material_name: 'Grade M40 Structural Concrete', required: '450,000 m³', available: '410,000 m³', short: '40,000 m³', risk_level: 'Medium' },
    { material_name: 'Penstock High Tensile Steel', required: '8,400 MT', available: '8,100 MT', short: '300 MT', risk_level: 'Low' },
  ])

  const procurementRisks = isNewEstimate ? [
    { item: `${estCapMw ? Math.round(estCapMw / (projectMeta?.number_of_units || 4)) : 250} MW Francis Turbine Runner`, vendor: 'BHEL Bhopal', lead_time_weeks: 24, risk: 'Low Risk' },
    { item: `Main Step-Up Transformer (${estCapMw ? Math.round(estCapMw * 1.2) : 300} MVA)`, vendor: 'ABB India', lead_time_weeks: 16, risk: 'Low Risk' },
    { item: 'Penstock Gate Valves (IS 2062)', vendor: 'Triveni Engineering', lead_time_weeks: 10, risk: 'Low Risk' },
  ] : (data?.procurement_risks || [
    { item: '250 MW Francis Turbine Runner', vendor: 'BHEL Bhopal', lead_time_weeks: 28, risk: 'Low Risk' },
    { item: 'Main Step-Up Transformer (300 MVA)', vendor: 'ABB India', lead_time_weeks: 18, risk: 'Medium Risk' },
    { item: 'Penstock Gate Valves (IS 2062)', vendor: 'Triveni Engineering', lead_time_weeks: 12, risk: 'Low Risk' },
  ])

  // Live Telemetry Benchmark Projects (HP-001, HP-002, HP-003)
  const liveBenchmarkIds = new Set(['HP-001', 'HP-002', 'HP-003'])
  const liveBenchmarks = [
    { id: 'HP-001', label: 'HP-001: Tehri Hydro Project (Uttarakhand)' },
    { id: 'HP-002', label: 'HP-002: Nathpa Jhakri Plant (Himachal)' },
    { id: 'HP-003', label: 'HP-003: Subansiri Lower Project (Arunachal)' },
  ]

  // Filter custom AI estimated projects from backend
  const customEstProjects = allProjectsList
    .filter((p) => p.project_id && p.project_id.startsWith('HP-EST-'))
    .map((p) => ({
      id: p.project_id,
      label: `✨ ${p.project_id}: ${p.project_name || 'AI Simulation Project'}`
    }))

  // Ensure current active estimation is included
  if (estimationResult?.project_id && !customEstProjects.some(c => c.id === estimationResult.project_id)) {
    const activeName = estimationResult.project_inputs?.project_name || 'Active Simulation'
    customEstProjects.unshift({
      id: estimationResult.project_id,
      label: `⚡ ${estimationResult.project_id}: ${activeName}`
    })
  }

  // All Other Benchmark Database Projects (HP-004 to HP-400)
  const otherBenchmarkProjects = allProjectsList
    .filter((p) => p.project_id && !p.project_id.startsWith('HP-EST-') && !liveBenchmarkIds.has(p.project_id))
    .slice(0, 50)
    .map((p) => ({
      id: p.project_id,
      label: `${p.project_id}: ${p.project_name}`
    }))

  return (
    <div>
      {/* Header Info & Project Selector */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '0.75rem' }}>
        <div>
          <div style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
            PROJECT TELEMETRY • LIVE AGENT MONITORING
          </div>
          <h1 className="results-title" style={{ fontSize: '1.75rem', marginTop: '2px' }}>
            Construction Status
          </h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
            Target Project:
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            style={{
              padding: '6px 12px',
              fontSize: '0.82rem',
              fontWeight: 700,
              background: '#FFFFFF',
              border: '1px solid #CBD5E1',
              borderRadius: '6px',
              color: '#0F172A',
              maxWidth: '340px'
            }}
          >
            <optgroup label="Live Benchmark Site Telemetry">
              {liveBenchmarks.map(opt => (
                <option key={opt.id} value={opt.id}>{opt.label}</option>
              ))}
            </optgroup>
            {customEstProjects.length > 0 && (
              <optgroup label="AI Estimated Projects (Planning Phase)">
                {customEstProjects.map(opt => (
                  <option key={opt.id} value={opt.id}>{opt.label}</option>
                ))}
              </optgroup>
            )}
            {otherBenchmarkProjects.length > 0 && (
              <optgroup label="Dataset Benchmark Projects">
                {otherBenchmarkProjects.map(opt => (
                  <option key={opt.id} value={opt.id}>{opt.label}</option>
                ))}
              </optgroup>
            )}
          </select>
          <button style={{ background: '#005F6A', color: '#FFFFFF', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}>
            Export Report
          </button>
        </div>
      </div>

      {/* 5 Monitoring Tabs */}
      <div className="monitoring-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab-link ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          ⚡ Connecting to Backend Agent Telemetry...
        </div>
      )}

      {error && (
        <div style={{ background: '#FFEBEE', color: '#D50000', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
          ⚠️ {error}
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Top 4 KPI Metric Block Row */}
          <div className="kpi-cards-grid">
            <div className="kpi-card">
              <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                OVERALL PROGRESS
              </div>
              <div className="stat-huge" style={{ fontSize: '1.9rem', margin: '4px 0' }}>
                {actualPct}% <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>/ {plannedPct}% Planned</span>
              </div>
              <div style={{ height: '6px', background: '#E2E8F0', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${actualPct}%`, height: '100%', background: '#005F6A' }} />
              </div>
            </div>

            <div className="kpi-card">
              <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                VARIANCE / STATUS 🕒
              </div>
              <div className="stat-huge" style={{ fontSize: '1.7rem', color: variancePct > 5 ? '#D50000' : '#00E676', margin: '4px 0' }}>
                {variancePct > 0 ? `-${variancePct.toFixed(1)}%` : `+${Math.abs(variancePct).toFixed(1)}%`}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {healthStatus}
              </div>
            </div>

            <div className="kpi-card">
              <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                PROJECT COST (CAPEX) 💳
              </div>
              <div className="stat-huge" style={{ fontSize: '1.7rem', color: '#005F6A', margin: '4px 0' }}>
                ₹ {capexCr ? Number(capexCr).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : '—'} Cr
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {projectMeta?.project_name || selectedProjectId}
              </div>
            </div>

            <div className="kpi-card">
              <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                ACTIVE TELEMETRY RISKS 🎯
              </div>
              <div className="stat-huge" style={{ fontSize: '1.9rem', margin: '4px 0' }}>
                {delayedCount} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Delayed Activities</span>
              </div>
              <div style={{ display: 'flex', gap: '4px', height: '4px', borderRadius: '2px', overflow: 'hidden', marginTop: '6px' }}>
                <div style={{ flex: redFlex, background: '#FF1744' }} />
                <div style={{ flex: amberFlex, background: '#FF9E00' }} />
                <div style={{ flex: greenFlex, background: '#00E676' }} />
              </div>
            </div>
          </div>

          {/* Middle Row: EVM Chart + Live Interactive Site Status Map */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
            {/* EVM S-Curve Chart */}
            <div className="card-box">
              <div className="card-box-header">
                <span className="card-box-title">Performance S-Curve (EVM)</span>
                <div style={{ display: 'flex', gap: '12px', fontSize: '0.72rem', fontWeight: 700 }}>
                  <span style={{ color: '#94A3B8' }}>● Planned Value (PV)</span>
                  <span style={{ color: '#005F6A' }}>● Earned Value (EV)</span>
                  <span style={{ color: '#D50000' }}>● Actual Cost (AC)</span>
                </div>
              </div>
              <div style={{ height: '240px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                <svg width="100%" height="220" viewBox="0 0 500 200">
                  <line x1="0" y1="50" x2="500" y2="50" stroke="#E2E8F0" strokeDasharray="4" />
                  <line x1="0" y1="100" x2="500" y2="100" stroke="#E2E8F0" strokeDasharray="4" />
                  <line x1="0" y1="150" x2="500" y2="150" stroke="#E2E8F0" strokeDasharray="4" />

                  {/* Dynamic curves based on actual vs planned pct */}
                  <path d="M 20 180 Q 200 160 350 50 T 480 30" fill="none" stroke="#94A3B8" strokeWidth="2" strokeDasharray="4" />
                  <path d={isNewEstimate ? "M 20 180 L 350 180" : `M 20 180 Q 200 168 350 ${180 - (actualPct * 1.3)}`} fill="none" stroke="#005F6A" strokeWidth="3" />
                  <path d={isNewEstimate ? "M 20 180 L 350 180" : `M 20 180 Q 200 158 350 ${180 - (plannedPct * 1.3)}`} fill="none" stroke="#D50000" strokeWidth="2.5" />

                  <circle cx="350" cy={isNewEstimate ? 180 : 180 - (actualPct * 1.3)} r="5" fill="#005F6A" />
                  <circle cx="350" cy={isNewEstimate ? 180 : 180 - (plannedPct * 1.3)} r="5" fill="#D50000" />
                </svg>
              </div>
            </div>

            {/* Interactive Live Site Status Map */}
            <SiteStatusMap compact={false} projectMeta={projectMeta} />
          </div>

          {/* Bottom Table: Dynamic Agent View Based on Active Tab */}
          <div className="card-box">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>
                  {activeTab === 'status' && 'Activity Work Package Breakdown'}
                  {activeTab === 'delays' && 'Critical Path Delay Detection'}
                  {activeTab === 'rootcause' && 'Geological & Monsoon Root Cause Analysis'}
                  {activeTab === 'materials' && 'Material Availability & Stock Inventory'}
                  {activeTab === 'procurement' && 'Procurement & Logistics Risk Radar'}
                </h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Real-time telemetry for {selectedProjectId}
                </div>
              </div>
            </div>

            {/* TAB 1: STATUS ACTIVITIES */}
            {activeTab === 'status' && (
              <table className="table-custom">
                <thead>
                  <tr>
                    <th>WORK PACKAGE / ACTIVITY</th>
                    <th>PLANNED %</th>
                    <th>ACTUAL %</th>
                    <th>VARIANCE</th>
                    <th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {activities.map((act, idx) => (
                    <tr key={idx}>
                      <td><strong>{act.name || act.activity_name}</strong></td>
                      <td>{act.planned_pct}%</td>
                      <td><strong style={{ color: '#005F6A' }}>{act.actual_pct}%</strong></td>
                      <td>{act.variance > 0 ? `-${act.variance}%` : `+${Math.abs(act.variance)}%`}</td>
                      <td>
                        <span className={`badge-stat ${act.status === 'On Track' ? 'emerald' : act.status === 'Minor Delay' ? 'cyan' : act.status === 'Not Started' ? '' : 'rose'}`}
                              style={act.status === 'Not Started' ? { background: '#F1F5F9', color: '#475569' } : {}}>
                          {act.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* TAB 2: DELAYS */}
            {activeTab === 'delays' && (
              <table className="table-custom">
                <thead>
                  <tr>
                    <th>DELAYED ACTIVITY</th>
                    <th>PLANNED %</th>
                    <th>ACTUAL %</th>
                    <th>DELAY DAYS</th>
                    <th>IMPACT LEVEL</th>
                  </tr>
                </thead>
                <tbody>
                  {delayedActivities.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                        🎉 No critical path delays detected. Project is in pre-construction / planning phase.
                      </td>
                    </tr>
                  ) : (
                    delayedActivities.map((act, idx) => (
                      <tr key={idx}>
                        <td><strong>{act.name || act.activity_name}</strong></td>
                        <td>{act.planned_pct}%</td>
                        <td><strong style={{ color: '#D50000' }}>{act.actual_pct}%</strong></td>
                        <td><strong style={{ color: '#D50000' }}>{act.delay_days || 14} Days</strong></td>
                        <td><span className="badge-stat rose">{act.impact || 'Critical'}</span></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}

            {/* TAB 3: ROOT CAUSE */}
            {activeTab === 'rootcause' && (
              <table className="table-custom">
                <thead>
                  <tr>
                    <th>ROOT CAUSE TYPE</th>
                    <th>DESCRIPTION</th>
                    <th>IMPACT</th>
                    <th>RECOMMENDED MITIGATION</th>
                  </tr>
                </thead>
                <tbody>
                  {contributingFactors.length === 0 ? (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                        🌱 No active geological or environmental risk factors. Project is in pre-construction / planning phase.
                      </td>
                    </tr>
                  ) : (
                    contributingFactors.map((item, idx) => (
                      <tr key={idx}>
                        <td><strong>{item.type || item.activity || item.name}</strong></td>
                        <td style={{ color: '#D50000', fontWeight: 600 }}>{item.description || item.cause || item.root_cause}</td>
                        <td><span className={`badge-stat ${item.impact === 'High' ? 'rose' : item.impact === 'Medium' ? 'amber' : 'emerald'}`}>{item.impact}</span></td>
                        <td>{item.mitigation}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            )}

            {/* TAB 4: MATERIALS */}
            {activeTab === 'materials' && (
              <table className="table-custom">
                <thead>
                  <tr>
                    <th>MATERIAL TYPE</th>
                    <th>REQUIRED (MT / m³)</th>
                    <th>AVAILABLE STOCK</th>
                    <th>SHORTAGE / DEFICIT</th>
                    <th>RISK LEVEL</th>
                  </tr>
                </thead>
                <tbody>
                  {materials.map((item, idx) => (
                    <tr key={idx}>
                      <td><strong>{item.material_name || item.name}</strong></td>
                      <td>{item.required}</td>
                      <td><strong style={{ color: '#005F6A' }}>{item.available}</strong></td>
                      <td style={{ color: item.risk_level === 'High' ? '#D50000' : '#0F172A' }}>{item.short}</td>
                      <td>
                        <span className={`badge-stat ${item.risk_level === 'High' ? 'rose' : item.risk_level === 'Medium' ? 'amber' : 'emerald'}`}>
                          {item.risk_level} Risk
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* TAB 5: PROCUREMENT */}
            {activeTab === 'procurement' && (
              <table className="table-custom">
                <thead>
                  <tr>
                    <th>PROCUREMENT ITEM</th>
                    <th>VENDOR / SUPPLIER</th>
                    <th>LEAD TIME (WEEKS)</th>
                    <th>PROCUREMENT RISK</th>
                  </tr>
                </thead>
                <tbody>
                  {procurementRisks.map((item, idx) => (
                    <tr key={idx}>
                      <td><strong>{item.item || item.name}</strong></td>
                      <td>{item.vendor}</td>
                      <td>{item.lead_time_weeks} Weeks</td>
                      <td><span className={`badge-stat ${item.risk.includes('High') ? 'rose' : item.risk.includes('Medium') ? 'amber' : 'emerald'}`}>{item.risk}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}
