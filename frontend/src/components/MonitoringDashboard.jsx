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
  const { estimationResult, projects, monitorProjectId, setMonitorProjectId, currentForm } = useStore()
  const selectedProjectId = monitorProjectId
  const setSelectedProjectId = setMonitorProjectId
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

  const handleExportPDF = () => {
    if (!window.html2pdf) {
      alert("PDF library is still loading. Please try again in a moment.");
      return;
    }

    const isCurrentStoreResult = estimationResult?.project_id === selectedProjectId
    const capacity = Number(projectMeta?.capacity_mw || estimationResult?.project_inputs?.capacity_mw || 45)
    const state = projectMeta?.state || estimationResult?.project_inputs?.state || 'Uttarakhand'
    const riverBasin = projectMeta?.river_basin || currentForm?.river_basin || 'Ganga Basin'
    const projectName = projectMeta?.project_name || estimationResult?.project_inputs?.project_name || 'Hydroelectric Power Plant'
    const plantType = projectMeta?.project_type || currentForm?.project_type || 'run-of-river'
    const turbineType = projectMeta?.turbine_type || currentForm?.turbine_type || 'Francis'
    const damType = projectMeta?.dam_type || currentForm?.dam_type || 'Concrete Gravity'
    const units = projectMeta?.number_of_units || currentForm?.number_of_units || 3
    const netHead = projectMeta?.net_head_m || currentForm?.net_head_m || 120
    const designFlow = projectMeta?.design_flow_m3s || currentForm?.design_flow_m3s || 42.5
    const tunnelLength = projectMeta?.tunnel_length_km || currentForm?.tunnel_length_km || 3.5
    const tunnelDia = projectMeta?.tunnel_diameter_m || currentForm?.tunnel_diameter_m || 4.8
    const penstockLength = projectMeta?.penstock_length_m || currentForm?.penstock_length_m || 250
    const penstockDia = projectMeta?.penstock_diameter_m || currentForm?.penstock_diameter_m || 2.5

    const fmt = (n, decimals = 0) => {
      if (n == null || isNaN(n)) return '—'
      return Number(n).toLocaleString('en-IN', { maximumFractionDigits: decimals })
    }

    const costCr = isCurrentStoreResult
      ? fmt(estimationResult.model_3_cost?.total_project_cost_cr, 1)
      : fmt(projectMeta?.project_cost_cr || projectMeta?.real_cost_cr || (capacity * 8.5), 1)

    const costPerMw = isCurrentStoreResult
      ? fmt(estimationResult.model_3_cost?.cost_per_mw_cr, 2)
      : fmt((projectMeta?.project_cost_cr || projectMeta?.real_cost_cr || (capacity * 8.5)) / capacity, 2)

    const genGwh = isCurrentStoreResult
      ? fmt(estimationResult.model_2_generation?.annual_generation_gwh, 0)
      : fmt(projectMeta?.annual_generation_gwh || (capacity * 4.2), 0)

    const plf = isCurrentStoreResult
      ? (estimationResult.model_2_generation?.capacity_factor_pct || (estimationResult.model_2_generation?.capacity_factor ? (estimationResult.model_2_generation?.capacity_factor * 100).toFixed(1) : '45.0'))
      : '45.0'

    const durationMonths = isCurrentStoreResult
      ? (estimationResult.model_4_duration?.construction_duration_months || 48)
      : 48

    const confidenceScore = isCurrentStoreResult
      ? (estimationResult.rag_confidence?.confidence_score_pct || 84.5)
      : 80.0

    const twins = isCurrentStoreResult
      ? (estimationResult.rag_confidence?.comparable_projects || [])
      : []

    const concreteVal = isCurrentStoreResult 
      ? fmt(estimationResult.model_1_materials?.concrete_m3)
      : fmt(capacity * 1500)
    const cementVal = isCurrentStoreResult
      ? fmt(estimationResult.model_1_materials?.cement_mt)
      : fmt(capacity * 350)
    const rebarVal = isCurrentStoreResult
      ? fmt(estimationResult.model_1_materials?.reinforcement_steel_mt || estimationResult.model_1_materials?.rebar_steel_mt)
      : fmt(capacity * 80)
    const structSteelVal = isCurrentStoreResult
      ? fmt(estimationResult.model_1_materials?.structural_steel_mt)
      : fmt(capacity * 40)
    const penstockVal = isCurrentStoreResult
      ? fmt(estimationResult.model_1_materials?.penstock_steel_mt)
      : fmt(capacity * 15)
    const aggregateVal = isCurrentStoreResult
      ? fmt(estimationResult.model_1_materials?.aggregate_m3)
      : fmt(capacity * 900)
    const sandVal = isCurrentStoreResult
      ? fmt(estimationResult.model_1_materials?.sand_m3)
      : fmt(capacity * 600)
    const excavationVal = isCurrentStoreResult
      ? fmt(estimationResult.model_1_materials?.excavation_m3)
      : fmt(capacity * 2500)

    const rawRebar = isCurrentStoreResult ? (estimationResult.model_1_materials?.reinforcement_steel_mt || estimationResult.model_1_materials?.rebar_steel_mt) : (capacity * 80)
    const rawConcrete = isCurrentStoreResult ? estimationResult.model_1_materials?.concrete_m3 : (capacity * 1500)
    const rawPenstock = isCurrentStoreResult ? estimationResult.model_1_materials?.penstock_steel_mt : (capacity * 15)

    const rebarPhaseQty = fmt(rawRebar ? rawRebar * 0.15 : 450)
    const concretePhaseQty = fmt(rawConcrete ? rawConcrete * 0.10 : 1200)
    const penstockPhaseQty = fmt(rawPenstock ? rawPenstock * 0.25 : 210)

    const htmlContent = `
      <div style="font-family: 'Inter', system-ui, sans-serif; color: #0F172A; padding: 25px; max-width: 800px; margin: 0 auto; background: #FFFFFF; box-sizing: border-box;">
        <!-- Header Banner -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #005F6A; padding-bottom: 15px; margin-bottom: 25px;">
          <div>
            <h1 style="color: #005F6A; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">CONSTRUCT<span style="color: #00E5FF;">IQ</span></h1>
            <div style="font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; margin-top: 4px;">Power Plant Engineering & Estimation Report</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 12px; font-weight: 700; color: #0F172A;">PROJECT ID: ${selectedProjectId}</div>
            <div style="font-size: 10px; color: #64748B; margin-top: 3px;">Date: ${new Date().toLocaleDateString('en-IN')}</div>
          </div>
        </div>

        <!-- Project Name Banner -->
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; margin-bottom: 25px;">
          <div style="font-size: 10px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Project Title</div>
          <div style="font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 2px;">
            ${projectName}
          </div>
        </div>

        <!-- Key Analytics Grid -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px;">
          <div style="background: #F0FDFA; border: 1px solid #CCFBF1; padding: 12px; border-radius: 8px; text-align: center; box-sizing: border-box;">
            <div style="font-size: 9px; font-weight: 800; color: #0F766E; text-transform: uppercase;">Total CapEx (Estimated)</div>
            <div style="font-size: 20px; font-weight: 800; color: #005F6A; margin-top: 4px;">₹ ${costCr} Cr</div>
            <div style="font-size: 9px; color: #0F766E; margin-top: 2px;">₹ ${costPerMw} Cr / MW</div>
          </div>
          <div style="background: #F0F9FF; border: 1px solid #E0F2FE; padding: 12px; border-radius: 8px; text-align: center; box-sizing: border-box;">
            <div style="font-size: 9px; font-weight: 800; color: #0369A1; text-transform: uppercase;">Annual Generation</div>
            <div style="font-size: 20px; font-weight: 800; color: #005F6A; margin-top: 4px;">${genGwh} GWh</div>
            <div style="font-size: 9px; color: #0369A1; margin-top: 2px;">PLF: ${plf}%</div>
          </div>
          <div style="background: #FDF2F8; border: 1px solid #FCE7F3; padding: 12px; border-radius: 8px; text-align: center; box-sizing: border-box;">
            <div style="font-size: 9px; font-weight: 800; color: #BE185D; text-transform: uppercase;">Timeline & Duration</div>
            <div style="font-size: 20px; font-weight: 800; color: #BE185D; margin-top: 4px;">${durationMonths} Months</div>
            <div style="font-size: 9px; color: #BE185D; margin-top: 2px;">~${(durationMonths / 12).toFixed(1)} Years</div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
          <!-- Technical Specifications -->
          <div>
            <h3 style="font-size: 13px; font-weight: 800; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 12px; color: #0F172A; text-transform: uppercase; letter-spacing: 0.02em;">Technical Specifications</h3>
            <table style="width: 100%; font-size: 11px; border-collapse: collapse;">
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">State / Region</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${state}</td></tr>
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">River / Basin</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${riverBasin}</td></tr>
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">Plant Capacity</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${capacity} MW</td></tr>
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">Number of Units</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${units} Units</td></tr>
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">Net Head / Flow</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${netHead} m / ${designFlow} m³/s</td></tr>
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">Turbine / Dam Type</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${turbineType} / ${damType}</td></tr>
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">Tunnel Length & Dia</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${tunnelLength} km (${tunnelDia} m Dia)</td></tr>
              <tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 6px 0; color: #64748B; font-weight: 500;">Penstock L & Dia</td><td style="padding: 6px 0; font-weight: 700; text-align: right;">${penstockLength} m (${penstockDia} m Dia)</td></tr>
            </table>
          </div>

          <!-- Statutory & RAG Verification -->
          <div>
            <h3 style="font-size: 13px; font-weight: 800; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 12px; color: #0F172A; text-transform: uppercase; letter-spacing: 0.02em;">Statutory & RAG Benchmarking</h3>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
              <div>
                <div style="font-size: 10px; font-weight: 800; color: #64748B; text-transform: uppercase;">RAG Confidence Score</div>
                <div style="font-size: 18px; font-weight: 800; color: #047857; margin-top: 2px;">${confidenceScore}%</div>
              </div>
              <div style="display: flex; gap: 4px;">
                <span style="font-size: 9px; background: #D1FAE5; color: #065F46; padding: 2px 6px; border-radius: 4px; font-weight: 700;">MoEFCC</span>
                <span style="font-size: 9px; background: #D1FAE5; color: #065F46; padding: 2px 6px; border-radius: 4px; font-weight: 700;">CEA</span>
              </div>
            </div>
            <div style="font-size: 10px; font-weight: 800; color: #64748B; text-transform: uppercase; margin-bottom: 6px;">Historical Benchmark Twins</div>
            <div style="font-size: 11px; line-height: 1.5;">
              ${twins.length === 0 ? '<div style="color: #64748B; font-style: italic;">No historical twins matched.</div>' : twins.map(t => `
                <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #E2E8F0; padding: 4px 0;">
                  <span style="font-weight: 600; color: #334155;">${t.project_name || t.id}</span>
                  <span style="color: #047857; font-weight: 700;">${t.capacity_mw ? `${t.capacity_mw} MW` : 'Matched'}</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Material Bill of Quantities (BOQ) -->
        <div style="margin-bottom: 30px;">
          <h3 style="font-size: 13px; font-weight: 800; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 12px; color: #0F172A; text-transform: uppercase; letter-spacing: 0.02em;">Material Bill of Quantities (BOQ)</h3>
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Concrete</div>
              <div style="font-size: 12px; font-weight: 800; color: #005F6A; margin-top: 3px;">${concreteVal} m³</div>
            </div>
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Cement</div>
              <div style="font-size: 12px; font-weight: 800; color: #0F172A; margin-top: 3px;">${cementVal} MT</div>
            </div>
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Rebar Steel</div>
              <div style="font-size: 12px; font-weight: 800; color: #0F172A; margin-top: 3px;">${rebarVal} MT</div>
            </div>
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Struct. Steel</div>
              <div style="font-size: 12px; font-weight: 800; color: #005F6A; margin-top: 3px;">${structSteelVal} MT</div>
            </div>
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Penstock Steel</div>
              <div style="font-size: 12px; font-weight: 800; color: #005F6A; margin-top: 3px;">${penstockVal} MT</div>
            </div>
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Aggregate</div>
              <div style="font-size: 12px; font-weight: 800; color: #0F172A; margin-top: 3px;">${aggregateVal} m³</div>
            </div>
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Sand</div>
              <div style="font-size: 12px; font-weight: 800; color: #0F172A; margin-top: 3px;">${sandVal} m³</div>
            </div>
            <div style="border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; text-align: center; box-sizing: border-box;">
              <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">Excavation</div>
              <div style="font-size: 12px; font-weight: 800; color: #D50000; margin-top: 3px;">${excavationVal} m³</div>
            </div>
          </div>
        </div>

        <!-- Procurement Lookahead -->
        <div style="margin-bottom: 25px;">
          <h3 style="font-size: 13px; font-weight: 800; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 12px; color: #0F172A; text-transform: uppercase; letter-spacing: 0.02em;">Material Procurement Lookahead</h3>
          <table style="width: 100%; font-size: 11px; border-collapse: collapse; text-align: left;">
            <thead>
              <tr style="background: #F8FAFC; border-bottom: 2px solid #E2E8F0;">
                <th style="padding: 8px; font-weight: 700; color: #334155;">Material / Spec</th>
                <th style="padding: 8px; font-weight: 700; color: #334155;">Phase Quantity</th>
                <th style="padding: 8px; font-weight: 700; color: #334155;">ETA</th>
                <th style="padding: 8px; font-weight: 700; color: #334155; text-align: right;">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr style="border-bottom: 1px solid #F1F5F9;">
                <td style="padding: 8px;">Rebar - Fe500D Grade (Apex Steel)</td>
                <td style="padding: 8px;">${rebarPhaseQty} MT</td>
                <td style="padding: 8px;">Phase 1 Immediate</td>
                <td style="padding: 8px; text-align: right; font-weight: 700; color: #005F6A;">PLANNED</td>
              </tr>
              <tr style="border-bottom: 1px solid #F1F5F9;">
                <td style="padding: 8px;">Ready-Mix Structural Concrete</td>
                <td style="padding: 8px;">${concretePhaseQty} m³</td>
                <td style="padding: 8px;">Phase 2 Site Pour</td>
                <td style="padding: 8px; text-align: right; font-weight: 700; color: #005F6A;">PLANNED</td>
              </tr>
              <tr style="border-bottom: 1px solid #F1F5F9;">
                <td style="padding: 8px;">High Tensile Penstock Steel Plates (E350)</td>
                <td style="padding: 8px;">${penstockPhaseQty} MT</td>
                <td style="padding: 8px;">Phase 3 Tunneling</td>
                <td style="padding: 8px; text-align: right; font-weight: 700; color: #005F6A;">PLANNED</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Footer Disclaimer -->
        <div style="border-top: 1px solid #E2E8F0; padding-top: 15px; text-align: center; font-size: 9px; color: #94A3B8; line-height: 1.5; margin-top: 30px;">
          ConstructIQ Power Plant Estimator AI System. This is an automatically generated technical report compiled using machine learning models and statutory regulatory databases. All figures are engineering estimations.
        </div>
      </div>
    `;

    const element = document.createElement('div');
    element.innerHTML = htmlContent;
    document.body.appendChild(element);

    const safeProjectName = projectName.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const opt = {
      margin:       10,
      filename:     `ConstructIQ_Estimation_Report_${safeProjectName || selectedProjectId}.pdf`,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true, logging: false },
      jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    window.html2pdf().from(element).set(opt).save().then(() => {
      document.body.removeChild(element);
    });
  }

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
          <button 
            onClick={handleExportPDF}
            style={{ background: '#005F6A', color: '#FFFFFF', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}
          >
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
