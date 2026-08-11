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
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', zIndex: 1100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#FFFFFF', borderRadius: '14px', width: '520px', padding: '1.75rem', boxShadow: '0 12px 32px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>⛰️ Geotechnical & Rock Mechanics Data</h2>
          <button onClick={onClose} style={{ border: 'none', background: 'none', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Himalayan Geological Q-System Rating & Tunneling Excavation Risk Profile (Uttarakhand Basin).
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.82rem' }}>
          <div style={{ background: '#F8FAFC', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ROCK QUALITY DESIGNATION</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#005F6A' }}>RQD 78% (Good)</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>TUNNEL BORING FEASIBILITY</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#00E676' }}>High Suitability</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>SEISMIC ZONE CLASSIFICATION</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#FF9E00' }}>Zone IV / Zone V</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>EXCAVATION SLOPE STABILITY</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#005F6A' }}>Factor of Safety 1.85</div>
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
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', zIndex: 1100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#FFFFFF', borderRadius: '14px', width: '520px', padding: '1.75rem', boxShadow: '0 12px 32px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>🍃 Environmental & PARIVESH Clearance Data</h2>
          <button onClick={onClose} style={{ border: 'none', background: 'none', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Ministry of Environment, Forest and Climate Change (MoEFCC) PARIVESH Compliance Specs.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.82rem' }}>
          <div style={{ background: '#E8F5E9', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: '#065F46', fontSize: '0.7rem', fontWeight: 800 }}>ENVIRONMENTAL CLEARANCE</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#047857' }}>Approved Stage-II</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>FOREST LAND DIVERSION</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#005F6A' }}>142.8 Hectares</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>CAT PLAN ALLOCATION</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#005F6A' }}>₹ 42.5 Cr</div>
          </div>
          <div style={{ background: '#F8FAFC', padding: '10px', borderRadius: '8px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>E-FLOW RELEASE NORM</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#005F6A' }}>15% Lean Season</div>
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

