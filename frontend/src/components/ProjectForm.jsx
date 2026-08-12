import React, { useState, useEffect } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'

const HYDRO_STATES = [
  'Uttarakhand', 'Himachal Pradesh', 'Jammu & Kashmir', 'Ladakh', 'Sikkim',
  'Arunachal Pradesh', 'Assam', 'Meghalaya', 'Kerala', 'Karnataka',
  'Maharashtra', 'Andhra Pradesh', 'Telangana', 'Odisha', 'Madhya Pradesh',
  'Gujarat', 'West Bengal'
]

const STATE_RIVER_BASINS = {
  'Uttarakhand': ['Ganga Basin', 'Alaknanda River', 'Bhagirathi River', 'Yamuna Basin', 'Mandakini River'],
  'Himachal Pradesh': ['Sutlej River Basin', 'Beas River Basin', 'Chenab River Basin', 'Ravi River Basin'],
  'Jammu & Kashmir': ['Chenab River Basin', 'Jhelum River Basin', 'Indus River Basin'],
  'Ladakh': ['Indus River Basin', 'Zanskar River Basin'],
  'Sikkim': ['Teesta River Basin', 'Rangeet River Basin'],
  'Arunachal Pradesh': ['Subansiri River Basin', 'Siang River Basin', 'Dibang River Basin', 'Kameng River Basin'],
  'Assam': ['Brahmaputra Basin', 'Kopili River Basin'],
  'Meghalaya': ['Kopili River Basin', 'Umiam River Basin'],
  'Kerala': ['Periyar River Basin', 'Chalakkudy River Basin', 'Pamba River Basin'],
  'Karnataka': ['Sharavathi River Basin', 'Cauvery River Basin', 'Krishna Basin'],
  'Maharashtra': ['Koyna River Basin', 'Krishna Basin', 'Godavari Basin'],
  'Andhra Pradesh': ['Krishna River Basin', 'Godavari River Basin', 'Penna River Basin'],
  'Telangana': ['Godavari River Basin', 'Krishna River Basin'],
  'Odisha': ['Mahanadi Basin', 'Indravati River Basin'],
  'Madhya Pradesh': ['Narmada River Basin', 'Sone River Basin'],
  'Gujarat': ['Narmada River Basin', 'Tapti River Basin'],
  'West Bengal': ['Teesta River Basin', 'Damodar River Basin']
}

const BASIN_TO_STATE_MAP = {
  'Ganga Basin': 'Uttarakhand',
  'Alaknanda River': 'Uttarakhand',
  'Bhagirathi River': 'Uttarakhand',
  'Yamuna Basin': 'Uttarakhand',
  'Mandakini River': 'Uttarakhand',
  'Sutlej River Basin': 'Himachal Pradesh',
  'Beas River Basin': 'Himachal Pradesh',
  'Ravi River Basin': 'Himachal Pradesh',
  'Chenab River Basin': 'Jammu & Kashmir',
  'Jhelum River Basin': 'Jammu & Kashmir',
  'Indus River Basin': 'Ladakh',
  'Zanskar River Basin': 'Ladakh',
  'Teesta River Basin': 'Sikkim',
  'Rangeet River Basin': 'Sikkim',
  'Subansiri River Basin': 'Arunachal Pradesh',
  'Siang River Basin': 'Arunachal Pradesh',
  'Dibang River Basin': 'Arunachal Pradesh',
  'Kameng River Basin': 'Arunachal Pradesh',
  'Brahmaputra Basin': 'Assam',
  'Kopili River Basin': 'Assam',
  'Umiam River Basin': 'Meghalaya',
  'Periyar River Basin': 'Kerala',
  'Chalakkudy River Basin': 'Kerala',
  'Pamba River Basin': 'Kerala',
  'Sharavathi River Basin': 'Karnataka',
  'Cauvery River Basin': 'Karnataka',
  'Krishna Basin': 'Andhra Pradesh',
  'Krishna River Basin': 'Andhra Pradesh',
  'Godavari Basin': 'Telangana',
  'Godavari River Basin': 'Telangana',
  'Penna River Basin': 'Andhra Pradesh',
  'Koyna River Basin': 'Maharashtra',
  'Narmada River Basin': 'Madhya Pradesh',
  'Sone River Basin': 'Madhya Pradesh',
  'Tapti River Basin': 'Gujarat',
  'Mahanadi Basin': 'Odisha',
  'Indravati River Basin': 'Odisha',
  'Damodar River Basin': 'West Bengal'
}

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
  project_name: '',
  river_basin: 'Ganga Basin',
  project_category: 'Medium Hydro',
  capacity_mw: '',
  number_of_units: '',
  gross_head_m: '',
  net_head_m: '',
  design_flow_m3s: '',
  dam_height_m: '',
  dam_length_m: '',
  tunnel_length_km: '',
  tunnel_diameter_m: '',
  penstock_length_m: '',
  penstock_diameter_m: '',
  tunnel_configuration: 'Underground',
  state: 'Uttarakhand',
  project_type: 'run-of-river',
  turbine_type: 'Francis',
  dam_type: 'Concrete Gravity',
  powerhouse_type: 'Underground',
  terrain_type: 'Mountainous'
}

export function ProjectForm() {
  const { setEstimationResult, setIsEstimating, setEstimationError, setCurrentForm, isEstimating } = useStore()
  const [form, setForm] = useState(DEFAULT_HYDRO)

  useEffect(() => {
    if (setCurrentForm) {
      setCurrentForm(form)
    }
  }, [form, setCurrentForm])

  const handleChange = (e) => {
    const { name, value } = e.target
    const numVal = value === '' ? '' : isNaN(value) ? value : parseFloat(value)

    setForm((f) => {
      const updated = { ...f, [name]: numVal }

      if (name === 'state' && typeof value === 'string') {
        const availableBasins = STATE_RIVER_BASINS[value] || ['Ganga Basin']
        updated.river_basin = availableBasins[0]
      }

      if (name === 'river_basin' && typeof value === 'string') {
        const mappedState = BASIN_TO_STATE_MAP[value]
        if (mappedState) {
          updated.state = mappedState
        }
      }

      // If Capacity MW or Net Head changes, dynamically re-calculate Flow & Category
      if (name === 'capacity_mw' && typeof numVal === 'number' && numVal > 0) {
        updated.project_category = getCategoryFromMw(numVal)
        updated.design_flow_m3s = calculateDesignFlow(numVal, updated.net_head_m || 120)
        // Auto-scale default dam/tunnel dimensions proportionally if needed
        if (numVal > 100) {
          updated.number_of_units = updated.number_of_units || 4
          updated.dam_height_m = updated.dam_height_m || 65
          updated.tunnel_length_km = updated.tunnel_length_km || 8.5
        } else if (numVal < 10) {
          updated.number_of_units = updated.number_of_units || 2
          updated.dam_height_m = updated.dam_height_m || 15
          updated.tunnel_length_km = updated.tunnel_length_km || 1.2
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

    const cap = parseFloat(form.capacity_mw) || 45.0
    const netHead = parseFloat(form.net_head_m) || 120.0
    const flow = parseFloat(form.design_flow_m3s) || calculateDesignFlow(cap, netHead)

    const payload = {
      ...form,
      capacity_mw: cap,
      net_head_m: netHead,
      gross_head_m: parseFloat(form.gross_head_m) || Math.round(netHead / 0.95),
      design_flow_m3s: flow,
      number_of_units: parseInt(form.number_of_units) || (cap > 100 ? 4 : cap < 10 ? 2 : 3),
      dam_height_m: parseFloat(form.dam_height_m) || (cap > 100 ? 65.0 : 45.0),
      dam_length_m: parseFloat(form.dam_length_m) || 180.0,
      tunnel_length_km: parseFloat(form.tunnel_length_km) || (cap > 100 ? 8.5 : 3.5),
      tunnel_diameter_m: parseFloat(form.tunnel_diameter_m) || 4.8,
      penstock_length_m: parseFloat(form.penstock_length_m) || 250.0,
      penstock_diameter_m: parseFloat(form.penstock_diameter_m) || 2.5,
    }

    try {
      const result = await api.estimate(payload)
      setEstimationResult(result)
    } catch (err) {
      let msg = 'Estimation failed. Please check backend server.'
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') {
        msg = detail
      } else if (Array.isArray(detail)) {
        msg = detail.map((d) => (typeof d === 'string' ? d : `${d.loc ? d.loc.join('.') : 'field'}: ${d.msg || JSON.stringify(d)}`)).join('; ')
      } else if (detail && typeof detail === 'object') {
        msg = detail.message || detail.msg || JSON.stringify(detail)
      } else if (err.message) {
        msg = err.message
      }
      setEstimationError(String(msg))
    } finally {
      setIsEstimating(false)
    }
  }

  const availableBasins = STATE_RIVER_BASINS[form.state] || ['Ganga Basin']

  return (
    <div className="form-panel">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 className="form-panel-title">Hydroelectric Project Estimator</h2>
      </div>

      <form onSubmit={handleSubmit}>
        {/* PROJECT INFO SECTION */}
        <div className="form-group-title">PROJECT INFO</div>

        <div className="form-field">
          <label>Project Name (Optional)</label>
          <input
            type="text"
            name="project_name"
            placeholder="e.g. Manikaran Hydro Stage II"
            value={form.project_name || ''}
            onChange={handleChange}
          />
        </div>

        <div className="form-field">
          <label>State / Region</label>
          <select name="state" value={form.state} onChange={handleChange}>
            {HYDRO_STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label>River / Basin</label>
          <select name="river_basin" value={form.river_basin || availableBasins[0]} onChange={handleChange}>
            {availableBasins.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label>Capacity (MW)</label>
          <input
            type="number"
            name="capacity_mw"
            placeholder="e.g. 45 MW (Number)"
            value={form.capacity_mw}
            onChange={handleChange}
            step="any"
            min="0"
          />
          <div style={{ fontSize: '0.68rem', color: '#005F6A', marginTop: '2px', fontWeight: 600 }}>
            Category: {form.project_category || 'Medium Hydro'}
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
            placeholder="e.g. 120 m (Number)"
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
            placeholder="e.g. 42.5 m³/s (Auto)"
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
            placeholder="e.g. 3.5 km (Number)"
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
              placeholder="e.g. 250 m"
              value={form.penstock_length_m}
              onChange={handleChange}
            />
          </div>
          <div className="form-field" style={{ flex: 1 }}>
            <label>Dia. (m)</label>
            <input
              type="number"
              name="penstock_diameter_m"
              placeholder="e.g. 2.5 m"
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
