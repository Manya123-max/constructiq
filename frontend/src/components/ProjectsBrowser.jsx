import React, { useState, useEffect } from 'react'
import { api } from '../api/client'

// Smart formatter: auto-selects decimal places based on value magnitude
function fmt(n) {
  if (n == null || isNaN(n)) return '—'
  const num = Number(n)
  if (num === 0) return '0'
  if (num < 0.01) return num.toFixed(4)   // Pico: 0.0004 MW
  if (num < 1) return num.toFixed(3)      // Micro: 0.004 MW
  if (num < 10) return num.toFixed(2)     // Small: 5.50 MW
  if (num < 100) return num.toFixed(1)    // Medium: 45.5 MW
  return Math.round(num).toLocaleString('en-IN')  // Large: 565 MW
}

export function ProjectsBrowser() {
  const [searchQuery, setSearchQuery] = useState('')
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.getProjects()
      .then((res) => setProjects(res.data || []))
      .catch(() => setError('Could not fetch hydro project database from backend.'))
      .finally(() => setLoading(false))
  }, [])

  const filteredProjects = projects.filter((p) => {
    const query = searchQuery.toLowerCase()
    return (
      (p.project_name || '').toLowerCase().includes(query) ||
      (p.project_id || '').toLowerCase().includes(query) ||
      (p.state || '').toLowerCase().includes(query) ||
      (p.primary_source || '').toLowerCase().includes(query) ||
      (p.project_type || '').toLowerCase().includes(query)
    )
  })

  return (
    <div style={{ padding: '0.5rem 0' }}>
      <div style={{ marginBottom: '1.25rem' }}>
        <h1 className="results-title" style={{ fontSize: '1.6rem' }}>Hydro Power Dataset Browser</h1>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          400 Constraint-based Hydroelectric Projects across 6 Categories (Large, Medium, Small, Mini, Micro, Pico) in 17 Indian States ({filteredProjects.length} Projects Shown)
        </p>
      </div>

      <div style={{ marginBottom: '1.25rem' }}>
        <input
          type="text"
          style={{
            width: '100%',
            padding: '10px 14px',
            fontSize: '0.85rem',
            background: '#FFFFFF',
            border: '1px solid #CBD5E1',
            borderRadius: '8px',
            outline: 'none'
          }}
          placeholder="Search by project name, ID, state, plant type, or government source..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {loading && (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          ⚡ Loading benchmark project database...
        </div>
      )}

      {error && (
        <div style={{ background: '#FFEBEE', color: '#D50000', padding: '1rem', borderRadius: '8px' }}>
          ⚠️ {error}
        </div>
      )}

      {!loading && !error && filteredProjects.length === 0 && (
        <div style={{ padding: '3rem', textAlign: 'center', background: '#FFFFFF', borderRadius: '10px' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔍</div>
          <div>No projects matching "{searchQuery}".</div>
        </div>
      )}

      {!loading && !error && filteredProjects.length > 0 && (
        <div className="card-box" style={{ padding: '0', overflowX: 'auto' }}>
          <table className="table-custom" style={{ fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: '#F8FAFC' }}>
                <th style={{ padding: '12px 14px', width: '90px' }}>Project ID</th>
                <th style={{ padding: '12px 14px', minWidth: '200px' }}>Project Name</th>
                <th style={{ padding: '12px 14px', width: '120px' }}>Category</th>
                <th style={{ padding: '12px 14px', width: '130px' }}>Plant Type</th>
                <th style={{ padding: '12px 14px', width: '140px' }}>State</th>
                <th style={{ padding: '12px 14px', width: '120px', textAlign: 'right' }}>Capacity (MW)</th>
                <th style={{ padding: '12px 14px', width: '70px', textAlign: 'right' }}>Units</th>
                <th style={{ padding: '12px 14px', width: '150px', textAlign: 'right' }}>Annual Energy (GWh)</th>
                <th style={{ padding: '12px 14px', width: '90px', textAlign: 'right' }}>Year</th>
                <th style={{ padding: '12px 14px', minWidth: '160px' }}>Statutory Provenance</th>
              </tr>
            </thead>
            <tbody>
              {filteredProjects.map((p) => {
                const categoryColor = {
                  'Large Hydro': 'emerald', 'Medium Hydro': 'cyan',
                  'Small Hydro': 'amber', 'Mini Hydro': 'rose',
                  'Micro Hydro': 'rose', 'Pico Hydro': 'rose'
                }[p.project_category] || 'cyan'
                return (
                <tr key={p.project_id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                  <td style={{ padding: '12px 14px', fontWeight: 800, color: '#005F6A' }}>
                    {p.project_id}
                  </td>
                  <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--text-dark)' }}>
                    {p.project_name}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span className={`badge-stat ${categoryColor}`} style={{ fontSize: '0.7rem' }}>
                      {p.project_category || 'Hydro'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span className="badge-stat cyan" style={{ fontSize: '0.7rem' }}>
                      💧 {p.project_type || 'run-of-river'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {p.state}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 800 }}>
                    {fmt(p.capacity_mw)}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                    {p.number_of_units ?? '—'}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 700 }}>
                    {fmt(p.annual_generation_gwh)}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right', color: 'var(--text-muted)' }}>
                    {p.commissioning_year || '—'}
                  </td>
                  <td style={{ padding: '12px 14px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {p.primary_source || 'CEA / PARIVESH / Synthetic v1.0'}
                  </td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
