import React, { useState } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'

const HYDRO_STATES = [
  'Uttarakhand', 'Himachal Pradesh', 'Jammu & Kashmir', 'Ladakh', 'Sikkim',
  'Arunachal Pradesh', 'Assam', 'Meghalaya', 'Kerala', 'Karnataka',
  'Maharashtra', 'Andhra Pradesh', 'Telangana', 'Odisha', 'Madhya Pradesh',
  'Gujarat', 'West Bengal'
]

function getCategoryFromMw(mw) {
  if (mw > 100) return 'Large Hydro'
  if (mw >= 25) return 'Medium Hydro'
  if (mw >= 5) return 'Small Hydro'
  if (mw >= 1) return 'Mini Hydro'
  if (mw >= 0.1) return 'Micro Hydro'
  return 'Pico Hydro'
}

function calculateDesignFlow(mw, head) {
  if (!mw || !head || head <= 0) return 45
  const flow = (mw * 1e6) / (1000.0 * 9.81 * head * 0.90)
  return Math.max(0.1, Math.round(flow * 10) / 10)
}

const DEFAULT_HYDRO = {
  project_category: 'Medium Hydro',
  capacity_mw: 45,
  number_of_units: 3,
  gross_head_m: 125,
  net_head_m: 120,
  design_flow_m3s: 42.5,
  dam_height_m: 45,
  dam_length_m: 180,
  tunnel_length_km: 3.5,
  tunnel_diameter_m: 4.8,
  penstock_length_m: 250,
  penstock_diameter_m: 2.5,
  tunnel_configuration: 'Underground',
  state: 'Uttarakhand',
  project_type: 'run-of-river',
  turbine_type: 'Francis',
  dam_type: 'Concrete Gravity',
  powerhouse_type: 'Underground',
  terrain_type: 'Mountainous'
}

export function ProjectForm() {
  const { setEstimationResult, setIsEstimating, setEstimationError, isEstimating } = useStore()
  const [form, setForm] = useState(DEFAULT_HYDRO)

  const handleChange = (e) => {
    const { name, value } = e.target
    const numVal = value === '' ? '' : isNaN(value) ? value : parseFloat(value)

    setForm((f) => {
      const updated = { ...f, [name]: numVal }

      // If Capacity MW or Net Head changes, dynamically re-calculate Flow & Category
      if (name === 'capacity_mw' && typeof numVal === 'number' && numVal > 0) {
        updated.project_category = getCategoryFromMw(numVal)
        updated.design_flow_m3s = calculateDesignFlow(numVal, updated.net_head_m || 120)
        // Auto-scale default dam/tunnel dimensions proportionally if needed
        if (numVal > 100) {
          updated.number_of_units = 4
          updated.dam_height_m = Math.max(65, updated.dam_height_m)
          updated.tunnel_length_km = Math.max(8.5, updated.tunnel_length_km)
        } else if (numVal < 10) {
          updated.number_of_units = 2
          updated.dam_height_m = Math.min(15, updated.dam_height_m || 15)
          updated.tunnel_length_km = Math.min(1.2, updated.tunnel_length_km || 1.2)
        }
      }

      if (name === 'net_head_m' && typeof numVal === 'number' && numVal > 0) {
        updated.gross_head_m = Math.round(numVal / 0.95)
        updated.design_flow_m3s = calculateDesignFlow(updated.capacity_mw || 45, numVal)
        // Turbine selection rule by net head
        if (numVal > 250) updated.turbine_type = 'Pelton'
        else if (numVal > 45) updated.turbine_type = 'Francis'
        else updated.turbine_type = 'Kaplan'
      }

      return updated
    })
  }

  const handleTunnelToggle = (config) => {
    setForm((f) => ({
      ...f,
      tunnel_configuration: config,
      powerhouse_type: config === 'Underground' ? 'Underground' : 'Surface',
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsEstimating(true)
    setEstimationError(null)

    // Ensure capacity_mw is a valid number
    const payload = {
      ...form,
      capacity_mw: parseFloat(form.capacity_mw) || 45.0,
      net_head_m: parseFloat(form.net_head_m) || 120.0,
      design_flow_m3s: parseFloat(form.design_flow_m3s) || calculateDesignFlow(form.capacity_mw, form.net_head_m),
    }

    try {
      const result = await api.estimate(payload)
      setEstimationResult(result)
    } catch (err) {
      setEstimationError(err.response?.data?.detail || 'Estimation failed. Please check backend server.')
    } finally {
      setIsEstimating(false)
    }
  }

  return (
    <div className="form-panel">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 className="form-panel-title">Hydroelectric Project Estimator</h2>
        <span style={{ fontSize: '1.2rem', cursor: 'pointer' }}>⚙️</span>
      </div>

      <form onSubmit={handleSubmit}>
        {/* PROJECT INFO SECTION */}
        <div className="form-group-title">PROJECT INFO</div>

        <div className="form-field">
          <label>State / Basin</label>
          <select name="state" value={form.state} onChange={handleChange}>
            {HYDRO_STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label>Capacity (MW)</label>
          <input
            type="number"
            name="capacity_mw"
            value={form.capacity_mw}
            onChange={handleChange}
            step="any"
            min="0"
          />
          <div style={{ fontSize: '0.68rem', color: '#005F6A', marginTop: '2px', fontWeight: 600 }}>
            Category: {form.project_category}
          </div>
        </div>

        <div className="form-field">
          <label>Dam Type</label>
          <select name="dam_type" value={form.dam_type} onChange={handleChange}>
            <option value="Concrete Gravity">Concrete Gravity</option>
            <option value="Barrage / Weir">Barrage / Weir</option>
            <option value="Rockfill">Rockfill</option>
            <option value="Arch Dam">Arch Dam</option>
          </select>
        </div>

        {/* HYDRAULIC PARAMETERS SECTION */}
        <div className="form-group-title">HYDRAULIC PARAMETERS</div>

        <div className="form-field">
          <label>Net Head (m) ⓘ</label>
          <input
            type="number"
            name="net_head_m"
            value={form.net_head_m}
            onChange={handleChange}
            step="any"
          />
        </div>

        <div className="form-field">
          <label>Design Flow (m³/s) ⓘ</label>
          <input
            type="number"
            name="design_flow_m3s"
            value={form.design_flow_m3s}
            onChange={handleChange}
            step="any"
          />
        </div>

        <div className="form-field">
          <label>Turbine Type</label>
          <select name="turbine_type" value={form.turbine_type} onChange={handleChange}>
            <option value="Francis">Francis</option>
            <option value="Pelton">Pelton</option>
            <option value="Kaplan">Kaplan</option>
            <option value="Cross-flow">Cross-flow</option>
          </select>
        </div>

        <div className="form-field">
          <label>Tunnel Configuration</label>
          <div className="toggle-group">
            <button
              type="button"
              className={`toggle-btn ${form.tunnel_configuration === 'Surface' ? 'active' : ''}`}
              onClick={() => handleTunnelToggle('Surface')}
            >
              Surface
            </button>
            <button
              type="button"
              className={`toggle-btn ${form.tunnel_configuration === 'Underground' ? 'active' : ''}`}
              onClick={() => handleTunnelToggle('Underground')}
            >
              Underground
            </button>
          </div>
        </div>

        <div className="form-field">
          <label>Tunnel Length (km)</label>
          <input
            type="number"
            name="tunnel_length_km"
            value={form.tunnel_length_km}
            onChange={handleChange}
            step="any"
          />
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <div className="form-field" style={{ flex: 1 }}>
            <label>Penstock L (m)</label>
            <input
              type="number"
              name="penstock_length_m"
              value={form.penstock_length_m}
              onChange={handleChange}
            />
          </div>
          <div className="form-field" style={{ flex: 1 }}>
            <label>Dia. (m)</label>
            <input
              type="number"
              name="penstock_diameter_m"
              value={form.penstock_diameter_m}
              onChange={handleChange}
              step="any"
            />
          </div>
        </div>

        <button type="submit" className="btn-simulation" disabled={isEstimating}>
          {isEstimating ? '⚡ Generating Project Estimate...' : '⚡ Generate Project Estimate'}
        </button>
      </form>
    </div>
  )
}
