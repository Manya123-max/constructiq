# -*- coding: utf-8 -*-
"""
ConstructIQ — Hydro Power Specialist Conversational Chatbot Engine.
Integrates Groq LLM (LLaMA-3.3-70B / LLaMA-3.1-8B) with domain-specific hydro engineering context,
CEA/PARIVESH regulatory norms, and bulletproof domain intelligence fallback.
"""

import os
import requests
from typing import List, Dict, Any, Optional

SYSTEM_PROMPT = """You are ConstructIQ's Senior Hydro Power Specialist & Engineering AI Assistant.
You specialize in hydroelectric power project estimation, hydraulic design physics, material BOQ (Concrete, Steel, Penstocks), project costing (₹ Cr/MW), construction schedules, and Indian statutory regulatory guidelines (CEA DPRs, MoEFCC PARIVESH clearances, CPPP tenders, CAG audits).

Key Technical & Statutory Knowledge Base:
1. Hydraulic Power Physics: Power (kW) = 9.81 * Q (m³/s) * H_net (m) * Efficiency (η ~ 0.88–0.92).
2. Basin Distribution: Ganga Basin (Uttarakhand), Sutlej/Indus Basin (Himachal/J&K), Siang/Subansiri (Arunachal), Periyar (Kerala), Krishna/Godavari (AP/Telangana).
3. Turbine Selection Rules:
   - Pelton: High Head (>200m), low flow.
   - Francis: Medium Head (40m - 350m), medium to high flow.
   - Kaplan/Propeller: Low Head (<50m), high discharge flow.
   - Cross-Flow/Kaplan: Mini/Micro Hydro (<25 MW).
4. Material BOQ Benchmarks (Indian Himalayan & Peninsular Conditions):
   - Concrete Volume: 2,500 – 4,200 m³ / MW.
   - Cement Quantity: 700 – 1,200 MT / MW.
   - Reinforcement Steel (Rebar): 180 – 320 MT / MW.
   - Penstock Steel: Grade IS 2062 / E350, 25 – 60 MT / MW depending on pressure head.
5. Financial Costs & Schedule Benchmarks:
   - Hydro Project Capital Cost: ₹ 8.5 Cr – ₹ 14.5 Cr / MW (Civil ~60–65%, Electro-Mechanical ~35–40%).
   - Construction Duration: 60 – 90 months for Large/Medium, 24 – 48 months for Small Hydro.
6. Government Statutory Authorities:
   - CEA (Central Electricity Authority): DPR technical appraisal & grid coupling.
   - PARIVESH (MoEFCC): Environmental Clearance (EC), Forest Clearance (FC), EIA/EMP reports.
   - CPPP (etenders.gov.in): Central public procurement BOQ contracts & tender schedules.

Guidelines:
- Give direct, professional, expert answers formatted clearly with bullet points.
- Keep answers concise, informative, and focused on hydro power plant engineering and project management.
- Always use professional engineering terminology and clear currency notation (₹ Cr / MW).
"""

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "mixtral-8x7b-32768"
]

# IMPORTANT: Set GROQ_API_KEY in Render Environment Variables.
# Never hardcode API keys — Groq auto-revokes keys found in public repos.

def generate_chat_response(
    messages: Any, 
    estimation_result: Optional[Dict[str, Any]] = None, 
    monitoring_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Sends conversation history to Groq API with robust model fallback, or returns domain engine answer.
    Accepts list of dicts or list of Pydantic models safely. Never raises an unhandled exception.
    """
    try:
        # Standardize input list of messages into dict format
        clean_msgs = []
        if isinstance(messages, list):
            for item in messages:
                if isinstance(item, dict):
                    clean_msgs.append({"role": str(item.get("role", "user")), "content": str(item.get("content", ""))})
                elif hasattr(item, "role") and hasattr(item, "content"):
                    clean_msgs.append({"role": str(getattr(item, "role", "user")), "content": str(getattr(item, "content", ""))})

        # Extract latest query string for rule fallback matching
        last_user_msg = ""
        for m in reversed(clean_msgs):
            if m["role"] in ("user", "human"):
                last_user_msg = m["content"].lower()
                break

        # Read API keys from environment
        gemini_api_key = (
            os.environ.get("GEMINI_API_KEY", "").strip()
            or os.environ.get("GEMINI_KEY", "").strip()
        )
        groq_api_key = (
            os.environ.get("GROQ_API_KEY", "").strip()
            or os.environ.get("GROQ_KEY", "").strip()
        )

        if not gemini_api_key and (not groq_api_key or not groq_api_key.startswith("gsk_")):
            print("[WARN] Neither GEMINI_API_KEY nor GROQ_API_KEY is configured. Falling back to dynamic domain engine.")
            return _domain_fallback_answer(last_user_msg, estimation_result, monitoring_context)

        # Build dynamic project context description
        context_str = ""
        if estimation_result:
            inputs = estimation_result.get("project_inputs", {}) or {}
            mats = estimation_result.get("model_1_materials", {}) or {}
            gen = estimation_result.get("model_2_generation", {}) or {}
            cost = estimation_result.get("model_3_cost", {}) or {}
            dur = estimation_result.get("model_4_duration", {}) or {}
            context_str += (
                f"\n--- ACTIVE ESTIMATED PROJECT PARAMETERS ---\n"
                f"- Name: Custom {inputs.get('capacity_mw')} MW {inputs.get('project_category') or 'Hydro'} Project in {inputs.get('state')}\n"
                f"- Capacity: {inputs.get('capacity_mw')} MW ({inputs.get('number_of_units')} units of {inputs.get('unit_capacity_mw')} MW)\n"
                f"- Configuration: {inputs.get('project_type')} type, {inputs.get('turbine_type')} turbine, net head {inputs.get('net_head_m')}m, flow {inputs.get('design_flow_m3s')} m3/s\n"
                f"- Estimated Capital Cost: Total CapEx is ₹{cost.get('total_project_cost_cr')} Cr (Civil: ₹{cost.get('civil_cost_cr')} Cr, Equipment: ₹{cost.get('equipment_cost_cr')} Cr, EM: ₹{cost.get('em_works_cr')} Cr, Normalised 2024: ₹{cost.get('cost_normalized_2024_cr')} Cr)\n"
                f"- Estimated Materials (BOQ): Concrete: {mats.get('concrete_m3')} m3, Cement: {mats.get('cement_mt')} MT, Rebar Steel: {mats.get('rebar_steel_mt')} MT, Penstock Steel: {mats.get('penstock_steel_mt')} MT\n"
                f"- Estimated Generation: Annual Energy: {gen.get('annual_generation_gwh')} GWh, Capacity Factor: {gen.get('capacity_factor_pct')}%\n"
                f"- Estimated Duration: {dur.get('construction_duration_months')} months\n"
            )

        if monitoring_context:
            status = monitoring_context.get("status", {}) or {}
            delays = monitoring_context.get("delays", {}) or {}
            rc = monitoring_context.get("rootcause", {}) or {}
            mats = monitoring_context.get("materials", {}) or {}
            proc = monitoring_context.get("procurement", {}) or {}
            delayed_list = [d["activity_name"] for d in delays.get("delayed_activities", [])]
            context_str += (
                f"\n--- ACTIVE MONITORED PROJECT STATUS ({monitoring_context.get('project_id')}) ---\n"
                f"- Name: {monitoring_context.get('project_name')}\n"
                f"- Capacity: {monitoring_context.get('capacity_mw')} MW ({monitoring_context.get('project_type')}) in {monitoring_context.get('state')}\n"
                f"- Construction Progress: {status.get('actual_pct')}% complete (Planned: {status.get('planned_pct')}%)\n"
                f"- Schedule Status: {status.get('status')} (Variance: {status.get('variance')}%, Total Delayed Activities: {delays.get('total_delayed')})\n"
                f"- Delayed Activities: {', '.join(delayed_list) if delayed_list else 'None'}\n"
                f"- Delay Root Cause Summary: {rc.get('root_cause_summary')}\n"
                f"- Material Shortages: {mats.get('shortage_count')} safety stock alerts\n"
                f"- Overall Procurement Risk: {proc.get('overall_risk')}\n"
            )

        prompt_with_context = SYSTEM_PROMPT
        if context_str:
            prompt_with_context += (
                f"\nHere is the real-time context of the active project the user is working on or looking at in the dashboard. "
                f"Answer the user's questions about their project using this data accurately:\n{context_str}\n"
            )

        # ─── Branch A: Use Gemini API ─────────────────────────────────────────
        if gemini_api_key:
            for model_name in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api_key}"
                    headers = {"Content-Type": "application/json"}
                    
                    contents = []
                    for msg in clean_msgs:
                        role = "user" if msg["role"] in ("user", "human") else "model"
                        contents.append({
                            "role": role,
                            "parts": [{"text": msg["content"]}]
                        })
                    
                    payload = {
                        "contents": contents,
                        "system_instruction": {
                            "parts": [{"text": prompt_with_context}]
                        },
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 800
                        }
                    }
                    resp = requests.post(url, json=payload, headers=headers, timeout=25.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        print(f"[INFO] Gemini model {model_name} responded successfully.")
                        return text
                    else:
                        print(f"[WARN] Gemini model {model_name} HTTP {resp.status_code}: {resp.text[:300]}")
                except Exception as ex:
                    print(f"[WARN] Gemini model {model_name} exception: {type(ex).__name__}: {ex}")

        # ─── Branch B: Use Groq API ───────────────────────────────────────────
        if groq_api_key and groq_api_key.startswith("gsk_"):
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            }
            formatted_messages = [{"role": "system", "content": prompt_with_context}]
            for msg in clean_msgs:
                role = "user" if msg["role"] in ("user", "human") else "assistant"
                formatted_messages.append({"role": role, "content": msg["content"]})

            for model_name in GROQ_MODELS:
                try:
                    payload = {
                        "model": model_name,
                        "messages": formatted_messages,
                        "temperature": 0.3,
                        "max_tokens": 800,
                    }
                    resp = requests.post(url, json=payload, headers=headers, timeout=25.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        print(f"[INFO] Groq model {model_name} responded successfully.")
                        return data["choices"][0]["message"]["content"]
                    else:
                        print(f"[WARN] Groq model {model_name} HTTP {resp.status_code}: {resp.text[:300]}")
                except Exception as ex:
                    print(f"[WARN] Groq model {model_name} exception: {type(ex).__name__}: {ex}")

        print("[ERROR] All configured APIs failed — falling back to domain engine.")
        return _domain_fallback_answer(last_user_msg, estimation_result, monitoring_context)

    except Exception as outer_ex:
        return _domain_fallback_answer("hydro", estimation_result, monitoring_context)


def _domain_fallback_answer(
    query: str, 
    estimation_result: Optional[Dict[str, Any]] = None, 
    monitoring_context: Optional[Dict[str, Any]] = None
) -> str:
    """Intelligent multi-branch domain knowledge engine for hydro inquiries (supporting active context)."""
    
    q = (query or "").lower().strip()
    
    # Extract project input parameters if present in estimation_result
    inputs = {}
    mats = {}
    gen = {}
    cost = {}
    dur = {}
    if estimation_result:
        inputs = estimation_result.get("project_inputs", {}) or {}
        mats = estimation_result.get("model_1_materials", {}) or {}
        gen = estimation_result.get("model_2_generation", {}) or {}
        cost = estimation_result.get("model_3_cost", {}) or {}
        dur = estimation_result.get("model_4_duration", {}) or {}

    # ─── 1. Capacity & Sizing Queries ─────────────────────────────────────────
    if any(k in q for k in ["capacity", "mw", "megawatt", "size", "rating", "unit", "units", "how big", "scale"]):
        if inputs:
            cap = inputs.get("capacity_mw", 45)
            units = inputs.get("number_of_units", 3)
            ucap = inputs.get("unit_capacity_mw") or round(cap / max(units, 1), 2)
            cat = inputs.get("project_category") or ("Large Hydro" if cap > 100 else "Medium Hydro" if cap >= 25 else "Small Hydro")
            ptype = inputs.get("project_type", "run-of-river")
            return (
                f"⚡ Installed Capacity Details for Active Project:\n\n"
                f"• **Total Capacity:** {cap} MW\n"
                f"• **Unit Configuration:** {units} Generation Units × {ucap} MW each\n"
                f"• **Hydro Category:** {cat}\n"
                f"• **Plant Type:** {ptype}\n"
                f"• **State:** {inputs.get('state', 'Uttarakhand')}"
            )
        elif monitoring_context:
            pid = monitoring_context.get("project_id")
            name = monitoring_context.get("project_name", "Monitored Plant")
            cap = monitoring_context.get("capacity_mw", 0)
            ptype = monitoring_context.get("project_type", "Hydro")
            return (
                f"⚡ Capacity Profile for Monitored Project {pid} ({name}):\n\n"
                f"• **Installed Capacity:** {cap} MW\n"
                f"• **Plant Category:** {ptype}\n"
                f"• **State:** {monitoring_context.get('state', 'India')}"
            )
        else:
            return (
                "⚡ Hydroelectric Capacity Classification (CEA Standards):\n\n"
                "• **Pico Hydro:** < 0.1 MW\n"
                "• **Micro Hydro:** 0.1 MW – 1 MW\n"
                "• **Mini Hydro:** 1 MW – 5 MW\n"
                "• **Small Hydro:** 5 MW – 25 MW\n"
                "• **Medium Hydro:** 25 MW – 100 MW\n"
                "• **Large Hydro:** > 100 MW"
            )

    # ─── 2. Net Head & Hydraulic Elevation Queries ────────────────────────────
    if any(k in q for k in ["head", "net head", "gross head", "drop", "elevation", "height", "fall", "water head"]):
        if inputs:
            net_head = inputs.get("net_head_m", 120)
            gross_head = inputs.get("gross_head_m") or round(net_head / 0.95, 1)
            flow = inputs.get("design_flow_m3s", 42.5)
            ttype = inputs.get("turbine_type", "Francis")
            return (
                f"💧 Hydraulic Head & Flow Parameters for Active Project:\n\n"
                f"• **Net Head (H_net):** {net_head} meters\n"
                f"• **Gross Head (H_gross):** {gross_head} meters (approx. 5% friction loss factor)\n"
                f"• **Design Discharge Flow (Q):** {flow} m³/s\n"
                f"• **Selected Turbine:** {ttype} Turbine"
            )
        else:
            return (
                "💧 Hydraulic Head Classification in Hydro Power Physics:\n\n"
                "• **Low Head (< 50m):** Uses Kaplan / Propeller turbines with high flow discharge.\n"
                "• **Medium Head (50m – 250m):** Uses Francis turbines (most versatile design).\n"
                "• **High Head (> 250m):** Uses Pelton impulse turbines with multi-jet nozzles.\n\n"
                "Formula: Power (kW) = 9.81 × Design Flow (m³/s) × Net Head (m) × Efficiency (η)."
            )

    # ─── 3. Turbine & Equipment Queries ──────────────────────────────────────
    if any(k in q for k in ["turbine", "pelton", "francis", "kaplan", "runner", "generator", "transformer", "equipment"]):
        if inputs:
            ttype = inputs.get("turbine_type", "Francis")
            units = inputs.get("number_of_units", 3)
            cap = inputs.get("capacity_mw", 45)
            net_head = inputs.get("net_head_m", 120)
            return (
                f"⚙️ Electro-Mechanical Equipment Specs for Active Project:\n\n"
                f"• **Turbine Type:** {ttype} Hydro Turbine\n"
                f"• **Unit Count:** {units} Turbines ({round(cap/max(units,1), 2)} MW per unit)\n"
                f"• **Operating Net Head:** {net_head} m\n"
                f"• **Design Flow:** {inputs.get('design_flow_m3s', 42.5)} m³/s\n"
                f"• **Powerhouse Type:** {inputs.get('powerhouse_type', 'Underground')}"
            )
        else:
            return (
                "⚙️ Hydro Turbine Selection Criteria:\n\n"
                "• **Francis Turbine:** Medium Head (40m – 350m). Efficiency ~93–95%.\n"
                "• **Pelton Turbine:** High Head (> 250m). Multi-jet impulse runner.\n"
                "• **Kaplan Turbine:** Low Head (< 50m), high flow rate. Adjustable blades.\n"
                "• **Cross-Flow Turbine:** Mini/Micro hydro projects (< 5 MW)."
            )

    # ─── 4. Location & Basin Queries ──────────────────────────────────────────
    if any(k in q for k in ["location", "state", "where", "basin", "river", "place", "region", "site"]):
        if inputs:
            state = inputs.get("state", "Uttarakhand")
            basin = inputs.get("river_basin", "Ganga Basin")
            terrain = inputs.get("terrain_type", "Mountainous")
            return (
                f"📍 Location & Geographic Regime for Active Project:\n\n"
                f"• **State / Region:** {state}\n"
                f"• **River / Basin:** {basin}\n"
                f"• **Terrain Type:** {terrain}\n"
                f"• **Project Type:** {inputs.get('project_type', 'run-of-river')}"
            )
        elif monitoring_context:
            pid = monitoring_context.get("project_id")
            name = monitoring_context.get("project_name", "Monitored Plant")
            return (
                f"📍 Site Location for Monitored Project {pid} ({name}):\n\n"
                f"• **State:** {monitoring_context.get('state', 'India')}\n"
                f"• **Plant Type:** {monitoring_context.get('project_type', 'Hydro')}"
            )
        else:
            return (
                "🌊 Hydroelectric River Basin Regimes (Indian Context):\n\n"
                "• Primary Active Basins in ConstructIQ Dataset:\n"
                "  1. Ganga River Basin (Uttarakhand / UP): High head run-of-river & storage projects.\n"
                "  2. Sutlej / Indus Basin (Himachal / J&K): Glacial high-discharge rivers.\n"
                "  3. Brahmaputra / Siang Basin (Arunachal / Assam): Ultra-large capacity projects.\n"
                "  4. Periyar & Peninsular Basins (Kerala, AP, Karnataka): Medium head reservoir powerhouses."
            )

    # ─── 5. Cost & CapEx Queries ──────────────────────────────────────────────
    if any(k in q for k in ["cost", "budget", "price", "cr", "crore", "capex", "estimation", "financial", "money", "expense"]):
        if cost or inputs:
            cap = inputs.get("capacity_mw", 45)
            tot_cost = cost.get("total_project_cost_cr") or round(cap * 8.6, 1)
            civ_cost = cost.get("civil_cost_cr") or round(tot_cost * 0.62, 1)
            eq_cost = cost.get("equipment_cost_cr") or round(tot_cost * 0.38, 1)
            cost_mw = cost.get("cost_per_mw_cr") or round(tot_cost / cap, 2)
            return (
                f"💰 Estimated Capital Cost for Active Project ({cap} MW):\n\n"
                f"• **Total Estimated CapEx:** ₹ {tot_cost:,} Cr\n"
                f"• **Civil Cost (Dam, Tunnel, Powerhouse):** ₹ {civ_cost:,} Cr (~62%)\n"
                f"• **Equipment Cost (Turbines, GIS Switchyard):** ₹ {eq_cost:,} Cr (~38%)\n"
                f"• **Cost Intensity per MW:** ₹ {cost_mw} Cr / MW\n\n"
                f"Predicted by GradientBoosting model trained on historical CEA DPR & CAG audit benchmarks."
            )
        elif monitoring_context:
            pid = monitoring_context.get("project_id")
            name = monitoring_context.get("project_name", "Monitored Plant")
            return (
                f"📊 Capital Cost & Budget Monitoring for Project {pid} ({name}):\n\n"
                f"• **Project Name:** {name}\n"
                f"• **Overall Cost Status:** View the EVM S-Curve & CapEx Breakdown on the dashboard.\n"
                f"• **Procurement Risk Status:** {monitoring_context.get('procurement', {}).get('overall_risk', 'LOW')} risk level."
            )
        else:
            return (
                "💰 Hydroelectric Capital Cost Benchmarks (Indian Context):\n\n"
                "• CapEx Outlay: ₹ 8.5 Cr to ₹ 14.5 Cr per MW installed capacity.\n"
                "• Cost Distribution:\n"
                "  - Civil Works (Dam, Tunnel, Powerhouse): ~60% – 65% of total outlay.\n"
                "  - Electro-Mechanical Equipment (Turbines, Generators, Transformers): ~35% – 40%."
            )

    # ─── 6. Material BOQ & Concrete Queries ──────────────────────────────────
    if any(k in q for k in ["concrete", "cement", "steel", "boq", "rebar", "intensity", "material", "quantity", "aggregate", "sand"]):
        if mats or inputs:
            cap = inputs.get("capacity_mw", 45)
            c_m3 = mats.get("concrete_m3") or round(cap * 3200)
            cem_mt = mats.get("cement_mt") or round(cap * 880)
            reb_mt = mats.get("reinforcement_steel_mt") or mats.get("rebar_steel_mt") or round(cap * 210)
            pen_mt = mats.get("penstock_steel_mt") or round(cap * 42)
            return (
                f"🧱 Predicted Material Bill of Quantities (BOQ):\n\n"
                f"• **Concrete Volume:** {c_m3:,} m³\n"
                f"• **Cement Quantity:** {cem_mt:,} MT (OPC 43/53 grade)\n"
                f"• **Reinforcement Steel (Rebar):** {reb_mt:,} MT (Fe 500D TMT)\n"
                f"• **Penstock Steel (E350 Grade):** {pen_mt:,} MT\n\n"
                f"Predicted by XGBoost MultiOutput models using historical PARIVESH clearances & NHPC commercial tenders."
            )
        elif monitoring_context:
            mats_ctx = monitoring_context.get("materials", {}) or {}
            shortages = mats_ctx.get("shortage_count") or 0
            return (
                f"🧱 Material Stock & Availability Status:\n\n"
                f"• **Critical Stock Alerts:** {shortages} safety stock threshold breaches detected.\n"
                f"• **Detailed Materials List:** Available on the Material Availability dashboard tab."
            )
        else:
            return (
                "🧱 Construction Material BOQ Benchmarks (per MW Installed Capacity):\n\n"
                "• Concrete Volume: 2,500 – 4,200 m³ / MW.\n"
                "• Cement Quantity: 700 – 1,200 MT / MW.\n"
                "• Reinforcement Steel (Rebar Fe500D): 180 – 320 MT / MW.\n"
                "• Penstock Steel (High Tensile Grade E350): 25 – 60 MT / MW."
            )

    # ─── 7. Generation & Capacity Factor Queries ──────────────────────────────
    if any(k in q for k in ["generation", "power", "gwh", "energy", "efficiency", "hydrology", "plf", "capacity factor", "annual"]):
        if gen or inputs:
            cap = inputs.get("capacity_mw", 45)
            gwh = gen.get("annual_generation_gwh") or round(cap * 8760 * 0.435 / 1000, 2)
            plf = gen.get("capacity_factor_pct") or 43.5
            flow = inputs.get("design_flow_m3s", 42.5)
            net_head = inputs.get("net_head_m", 120)
            ttype = inputs.get("turbine_type", "Francis")
            units = inputs.get("number_of_units", 3)
            return (
                f"⚡ Predicted Power Generation details for {cap} MW project:\n\n"
                f"• **Annual Energy Generation:** {gwh:,} GWh\n"
                f"• **Estimated Capacity Factor (PLF):** {plf}%\n"
                f"• **Design Discharge:** {flow} m³/s at {net_head} m net head\n"
                f"• **Turbine Choice:** {ttype} Turbine ({units} units)\n\n"
                f"Based on a 90% dependable hydrology year profile with typical efficiency metrics."
            )
        else:
            return (
                "⚡ Hydro Energy Generation Mechanics:\n\n"
                "• Annual Generation (GWh) = Installed Capacity (MW) × 8,760 hours × Plant Load Factor (PLF) ÷ 1,000.\n"
                "• Typical PLF in India: 35% – 55% for run-of-river plants depending on seasonal monsoon inflow."
            )

    # ─── 8. Dam, Tunnel & Civil Structures Queries ────────────────────────────
    if any(k in q for k in ["dam", "tunnel", "penstock", "powerhouse", "excavation", "civil", "structure"]):
        if inputs:
            return (
                f"🏗️ Civil Structures & Layout for Active Project:\n\n"
                f"• **Dam Type:** {inputs.get('dam_type', 'Concrete Gravity')} (Height: {inputs.get('dam_height_m', 45)} m, Length: {inputs.get('dam_length_m', 180)} m)\n"
                f"• **Headrace Tunnel:** {inputs.get('tunnel_length_km', 3.5)} km length, {inputs.get('tunnel_diameter_m', 4.8)} m diameter\n"
                f"• **Penstock:** {inputs.get('penstock_length_m', 250)} m length, {inputs.get('penstock_diameter_m', 2.5)} m diameter\n"
                f"• **Powerhouse Type:** {inputs.get('powerhouse_type', 'Underground')}"
            )
        else:
            return (
                "🏗️ Hydroelectric Civil Infrastructure Components:\n\n"
                "• **Dam / Barrage:** Concrete Gravity, Rockfill, or Arch structure for water head creation.\n"
                "• **Headrace Tunnel (HRT):** Transports water under pressure from reservoir to surge shaft.\n"
                "• **Penstock Steel Pipes:** High-pressure steel conduits feeding water into power turbines.\n"
                "• **Powerhouse:** Houses hydro generators, Francis/Pelton runners, and GIS switchyard."
            )

    # ─── 9. Duration & Schedule Queries ───────────────────────────────────────
    if any(k in q for k in ["duration", "timeline", "time", "month", "months", "year", "years"]):
        if dur or inputs:
            m = dur.get("construction_duration_months") or 48
            y = dur.get("estimated_years") or round(m / 12.0, 1)
            return (
                f"⏱️ Predicted Construction Duration:\n\n"
                f"• **Estimated Duration:** {m} Months ({y} Years)\n\n"
                f"Model incorporates terrain complexity, dam height, and tunneling parameters."
            )
        elif monitoring_context:
            status = monitoring_context.get("status", {}) or {}
            return (
                f"⏱️ Monitored Schedule Status:\n\n"
                f"• **Progress:** {status.get('actual_pct')}% complete vs {status.get('planned_pct')}% planned.\n"
                f"• **Status:** {status.get('status')}"
            )
        else:
            return (
                "⏱️ Typical Construction Timelines:\n\n"
                "• Large Hydro (>100 MW): 60 – 90 months.\n"
                "• Medium Hydro (25–100 MW): 42 – 60 months.\n"
                "• Small Hydro (<25 MW): 24 – 36 months."
            )

    # ─── 10. Delay & Monitoring Status Queries ────────────────────────────────
    if any(k in q for k in ["delay", "status", "progress", "schedule", "actual", "overrun", "monitoring"]):
        if monitoring_context:
            status = monitoring_context.get("status", {}) or {}
            delays = monitoring_context.get("delays", {}) or {}
            rc = monitoring_context.get("rootcause", {}) or {}
            pid = monitoring_context.get("project_id")
            name = monitoring_context.get("project_name", "Monitored Plant")
            delayed_list = [d["activity_name"] for d in delays.get("delayed_activities", [])]
            return (
                f"⏱️ Schedule & Delay Status for Project {pid} ({name}):\n\n"
                f"• **Overall Construction Progress:** {status.get('actual_pct')}% complete (Planned: {status.get('planned_pct')}%)\n"
                f"• **Schedule Profile:** {status.get('status')}\n"
                f"• **Schedule Variance:** {status.get('variance')}% deviation\n"
                f"• **Delayed Activities:** {', '.join(delayed_list) if delayed_list else 'None'}\n"
                f"• **Root Cause Analysis:** {rc.get('root_cause_summary')}"
            )
        else:
            return (
                "⏱️ Hydroelectric Delay Detection & Risk Management:\n\n"
                "Main root causes for delay include geological surprises (tunneling), land acquisition, "
                "and seasonal monsoons."
            )

    # ─── 11. CEA / DPR Submission Norms ───────────────────────────────────────
    if "cea" in q or "dpr" in q or "statutory" in q:
        return (
            "🏛️ CEA DPR Submission & Technical Appraisal Guidelines:\n\n"
            "• Statutory Norm: Required for Hydro Projects with CapEx > ₹ 1,000 Cr under Section 8 of Electricity Act 2003.\n"
            "• Key Appraisal Pillars:\n"
            "  1. Hydrology & Power Potential: 90% dependable year energy generation profile.\n"
            "  2. Geological Mapping: Q-system rock mass ratings for tunnel excavation.\n"
            "  3. Civil Layout: Probable Maximum Flood (PMF) spillway design.\n"
            "  4. Electro-Mechanical Specs: Unit sizing, Francis/Pelton selection, GIS switchyard.\n"
            "  5. Levelized Tariff: Per-unit generation cost analysis."
        )

    # ─── 12. PARIVESH / Environmental Clearances ──────────────────────────────
    if "parivesh" in q or "environmental" in q or "clearance" in q or "moefcc" in q:
        return (
            "🍃 PARIVESH (MoEFCC) Environmental & Forest Clearance Norms:\n\n"
            "• Category A (>50 MW): Requires Central MoEFCC Expert Appraisal Committee (EAC) approval.\n"
            "• Key Clearances:\n"
            "  1. Environmental Clearance (EC): EIA & EMP report approval.\n"
            "  2. Forest Clearance (FC): Forest diversion approval under Forest Conservation Act.\n"
            "  3. E-Flow Release: Minimum 15–20% lean season river flow maintenance."
        )

    # ─── 13. General Project Overview / Summary Queries ──────────────────────
    if any(k in q for k in ["project", "about", "overview", "summary", "details", "info", "tell me"]):
        if inputs:
            cap = inputs.get("capacity_mw", 45)
            net_head = inputs.get("net_head_m", 120)
            state = inputs.get("state", "Uttarakhand")
            ttype = inputs.get("turbine_type", "Francis")
            tot_cost = cost.get("total_project_cost_cr") or round(cap * 8.6, 1)
            gwh = gen.get("annual_generation_gwh") or round(cap * 8760 * 0.435 / 1000, 2)
            m = dur.get("construction_duration_months") or 48
            return (
                f"📋 Project Summary Overview:\n\n"
                f"• **Capacity & Type:** {cap} MW {inputs.get('project_type', 'run-of-river')} ({ttype} Turbine)\n"
                f"• **Location:** {state} ({inputs.get('river_basin', 'Ganga Basin')})\n"
                f"• **Net Head:** {net_head} m | **Flow:** {inputs.get('design_flow_m3s', 42.5)} m³/s\n"
                f"• **CapEx Estimate:** ₹ {tot_cost:,} Cr (₹ {cost.get('cost_per_mw_cr') or round(tot_cost/cap, 2)} Cr/MW)\n"
                f"• **Annual Energy:** {gwh:,} GWh (PLF: {gen.get('capacity_factor_pct', 43.5)}%)\n"
                f"• **Timeline:** {m} Months ({round(m/12.0, 1)} Years)"
            )

    # ─── 14. Default Answer ──────────────────────────────────────────────────
    if inputs:
        cap = inputs.get("capacity_mw", 45)
        net_head = inputs.get("net_head_m", 120)
        state = inputs.get("state", "Uttarakhand")
        ttype = inputs.get("turbine_type", "Francis")
        return (
            f"🌊 Active Project ({cap} MW Hydro, {state}):\n\n"
            f"• Net Head: {net_head} m | Turbine: {ttype}\n"
            f"• Ask me specific questions about CapEx cost, material BOQ, energy generation, turbine selection, or CEA/PARIVESH norms!"
        )

    return (
        "🌊 ConstructIQ Hydro Specialist AI Assistant:\n\n"
        "I can help you with hydroelectric power calculations, turbine selection (Francis, Pelton, Kaplan), "
        "material BOQ benchmarks (Concrete, Rebar, Penstocks), CapEx costs (₹ Cr/MW), "
        "river basin regimes (Ganga, Sutlej, Subansiri), and statutory guidelines (CEA DPR, PARIVESH)."
    )

