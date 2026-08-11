import React, { useState } from 'react'
import { useStore } from './store/useStore'
import { Logo } from './components/Logo'
import { ProjectForm } from './components/ProjectForm'
import { EstimationPanel } from './components/EstimationPanel'
import { MonitoringDashboard } from './components/MonitoringDashboard'
import { ProjectsBrowser } from './components/ProjectsBrowser'
import { HydroChatWidget } from './components/HydroChatWidget'
import './index.css'

function TopHeader() {
  return (
    <header className="top-header">
      <div className="header-left">
        <Logo showText={true} />
      </div>

      <div className="header-right">
        <div className="user-profile">
          <div className="avatar-circle">SE</div>
          <span>SR. ENGINEER</span>
        </div>
      </div>
    </header>
  )
}

function LeftDrawer({ onOpenGeoModal, onOpenEnvModal }) {
  const { activePage, setActivePage } = useStore()

  return (
    <aside className="left-drawer">
      <div>
        <div className="drawer-section-title">Technical Parameters</div>
        <button
          className={`drawer-nav-item ${activePage === 'estimate' ? 'active' : ''}`}
          onClick={() => setActivePage('estimate')}
        >
          Project Estimation
        </button>
        <button
          className={`drawer-nav-item ${activePage === 'monitor' ? 'active' : ''}`}
          onClick={() => setActivePage('monitor')}
        >
          Construction Status
        </button>
        <button
          className={`drawer-nav-item ${activePage === 'projects' ? 'active' : ''}`}
          onClick={() => setActivePage('projects')}
        >
          Project Overview
        </button>
      </div>

      <div>
        <div className="drawer-section-title">Site Data</div>
        <button
          className="drawer-nav-item"
          onClick={onOpenGeoModal}
        >
          Geotechnical
        </button>
        <button
          className="drawer-nav-item"
          onClick={onOpenEnvModal}
        >
          Environmental
        </button>
      </div>
    </aside>
  )
}

function GeotechnicalModal({ onClose }) {
  const { estimationResult, currentForm } = useStore()
  const capacityMw = Number(estimationResult?.project_inputs?.capacity_mw || currentForm?.capacity_mw || 250)
  const state = estimationResult?.project_inputs?.state || currentForm?.state || 'Uttarakhand'
  const terrainComplexity = Number(estimationResult?.project_inputs?.terrain_complexity_score || currentForm?.terrain_complexity_score || 3.5)
  const civilComplexity = Number(estimationResult?.project_inputs?.civil_complexity_score || currentForm?.civil_complexity_score || 3.8)

  const rqd = Math.max(35, Math.min(95, Math.round(110 - (terrainComplexity * 15) - (civilComplexity * 5))))
  let rqdRating = 'Poor'
  let rqdColor = '#D50000'
  if (rqd >= 90) { rqdRating = 'Excellent'; rqdColor = '#00E676' }
  else if (rqd >= 75) { rqdRating = 'Good'; rqdColor = '#005F6A' }
  else if (rqd >= 50) { rqdRating = 'Fair'; rqdColor = '#FF9E00' }

  let tbmSuitability = 'Low Suitability'
  let tbmColor = '#D50000'
  let tbmDesc = 'Requires steel rib supports and pressure grouting.'
  if (rqd >= 75) {
    tbmSuitability = 'High Suitability'
    tbmColor = '#00E676'
    tbmDesc = 'Minimal support. TBM excavation highly feasible.'
  } else if (rqd >= 50) {
    tbmSuitability = 'Medium Suitability'
    tbmColor = '#FF9E00'
    tbmDesc = 'Requires rock bolting and shotcrete lining.'
  }

  const isHimalayan = ['Uttarakhand', 'Himachal Pradesh', 'Sikkim', 'Arunachal Pradesh', 'Jammu & Kashmir'].includes(state)
  const seismicZone = isHimalayan ? 'Zone V (Very High Risk)' : 'Zone IV (High Risk)'
  const seismicColor = isHimalayan ? '#D50000' : '#FF9E00'
  const damRecommendation = isHimalayan 
    ? 'Flexible Rockfill Dam / Gravity with seismic joints' 
    : 'Concrete Gravity Dam'

  const fos = Math.max(1.10, Math.min(2.20, Number((2.4 - (terrainComplexity * 0.15) - (civilComplexity * 0.08)).toFixed(2))))
  let fosRating = 'Stable'
  let fosColor = '#005F6A'
  if (fos < 1.30) {
    fosRating = 'Critical (Requires anchors)'
    fosColor = '#D50000'
  } else if (fos < 1.50) {
    fosRating = 'Marginally Stable'
    fosColor = '#FF9E00'
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', zIndex: 1100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#FFFFFF', borderRadius: '14px', width: '560px', padding: '1.75rem', boxShadow: '0 12px 32px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>⛰️ Geotechnical & Rock Mechanics Data</h2>
          <button onClick={onClose} style={{ border: 'none', background: 'none', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
        </div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.4' }}>
          Dynamic Rock Mechanics rating based on <strong>{state}</strong> complexity ratings (Terrain: {terrainComplexity}, Civil: {civilComplexity}).
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.82rem' }}>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: `4px solid ${rqdColor}` }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>Rock Quality Designation</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>RQD {rqd}% ({rqdRating})</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Indicates fracturing & rock mass durability.</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: `4px solid ${tbmColor}` }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>Tunnel Boring Feasibility</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>{tbmSuitability}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{tbmDesc}</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: `4px solid ${seismicColor}` }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>Seismic Zone Classification</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>{seismicZone}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Recommendation: {damRecommendation}</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: `4px solid ${fosColor}` }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>Slope Stability (Safety Factor)</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>FoS {fos} ({fosRating})</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Mountain slope landslide resistance coefficient.</div>
          </div>
        </div>
        <button onClick={onClose} style={{ marginTop: '1.5rem', width: '100%', padding: '10px', background: '#005F6A', color: '#FFFFFF', border: 'none', borderRadius: '6px', fontWeight: 700, cursor: 'pointer' }}>
          Close Geotechnical View
        </button>
      </div>
    </div>
  )
}

function EnvironmentalModal({ onClose }) {
  const { estimationResult, currentForm } = useStore()
  const capacityMw = Number(estimationResult?.project_inputs?.capacity_mw || currentForm?.capacity_mw || 250)
  const state = estimationResult?.project_inputs?.state || currentForm?.state || 'Uttarakhand'
  const designFlow = Number(estimationResult?.project_inputs?.design_flow_m3s || currentForm?.design_flow_m3s || 162.5)
  const reservoirVolume = Number(estimationResult?.project_inputs?.reservoir_volume_mcm || currentForm?.reservoir_volume_mcm || 120.0)
  const totalCostCr = Number(estimationResult?.model_3_cost?.total_project_cost_cr || (capacityMw * 8.5))

  const isHimalayan = ['Uttarakhand', 'Himachal Pradesh', 'Sikkim', 'Arunachal Pradesh', 'Jammu & Kashmir'].includes(state)
  const stageApproved = capacityMw < 150 ? 'Approved Stage-II' : 'Approved Stage-I (Stage-II Pending)'
  const stageColor = capacityMw < 150 ? '#047857' : '#FF9E00'
  const clearanceDesc = capacityMw < 150 
    ? 'Full environmental clearance active' 
    : 'Forest land diversion finalized; Stage-II pending compliance audit'

  const forestHectares = (capacityMw * 0.4 + reservoirVolume * 0.25).toFixed(1)
  const catCost = (totalCostCr * 0.05 + capacityMw * 0.03).toFixed(1)

  const leanSeasonPct = isHimalayan ? 20 : 15
  const eflowReleaseVal = (designFlow * (leanSeasonPct / 100)).toFixed(1)

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', zIndex: 1100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#FFFFFF', borderRadius: '14px', width: '560px', padding: '1.75rem', boxShadow: '0 12px 32px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>🍃 Environmental & PARIVESH Clearance Data</h2>
          <button onClick={onClose} style={{ border: 'none', background: 'none', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
        </div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.4' }}>
          Statutory PARIVESH portal registry details for <strong>{state}</strong> ({capacityMw} MW Plant capacity).
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.82rem' }}>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: `4px solid ${stageColor}` }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>Environmental Clearance</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>{stageApproved}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{clearanceDesc}</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: '4px solid #005F6A' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>Forest Land Diversion</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>{forestHectares} Hectares</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Forest land area diverted under compensatory scheme.</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: '4px solid #005F6A' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>CAT Plan Allocation</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>₹ {catCost} Cr</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Catchment Area Treatment funding for afforestation.</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '12px', borderRadius: '8px', borderLeft: '4px solid #005F6A' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase' }}>E-Flow Release Norm</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', marginTop: '3px' }}>{leanSeasonPct}% ({eflowReleaseVal} m³/s)</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Mandatory continuous flow rate past the dam structures.</div>
          </div>
        </div>
        <button onClick={onClose} style={{ marginTop: '1.5rem', width: '100%', padding: '10px', background: '#005F6A', color: '#FFFFFF', border: 'none', borderRadius: '6px', fontWeight: 700, cursor: 'pointer' }}>
          Close Environmental View
        </button>
      </div>
    </div>
  )
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("ConstructIQ Component Error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', background: '#FFF5F5', border: '1.5px solid #FEB2B2', borderRadius: '12px', margin: '2rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>⚠️</div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#C53030', marginBottom: '0.5rem' }}>Application Render Error</h2>
          <p style={{ fontSize: '0.85rem', color: '#4A5568', marginBottom: '1.25rem', maxWidth: '500px', margin: '0 auto 1.25rem auto' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred. Click reload to refresh.'}
          </p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload() }}
            style={{ background: '#005F6A', color: '#FFFFFF', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '0.88rem' }}
          >
            🔄 Reload Application
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  const activePage = useStore((s) => s.activePage)
  const [showGeoModal, setShowGeoModal] = useState(false)
  const [showEnvModal, setShowEnvModal] = useState(false)

  return (
    <ErrorBoundary>
      <TopHeader />
      <div className="app-layout">
        <LeftDrawer
          onOpenGeoModal={() => setShowGeoModal(true)}
          onOpenEnvModal={() => setShowEnvModal(true)}
        />
        <main className="main-content">
          <ErrorBoundary>
            {activePage === 'estimate' && (
              <>
                <ProjectForm />
                <EstimationPanel />
              </>
            )}
            {activePage === 'monitor' && (
              <div className="workspace-panel">
                <MonitoringDashboard />
              </div>
            )}
            {activePage === 'projects' && (
              <div className="workspace-panel">
                <ProjectsBrowser />
              </div>
            )}
          </ErrorBoundary>
        </main>
      </div>

      {showGeoModal && <GeotechnicalModal onClose={() => setShowGeoModal(false)} />}
      {showEnvModal && <EnvironmentalModal onClose={() => setShowEnvModal(false)} />}

      <HydroChatWidget />
    </ErrorBoundary>
  )
}

