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
    
    # ─── 1. Cost & CapEx Queries ──────────────────────────────────────────────
    if any(k in query for k in ["cost", "budget", "price", "cr", "crore", "capex", "estimation", "financial"]):
        if estimation_result:
            inputs = estimation_result.get("project_inputs", {}) or {}
            cost = estimation_result.get("model_3_cost", {}) or {}
            cap = inputs.get("capacity_mw", 100)
            return (
                f"💰 Estimated Capital Cost for your Custom Project ({cap} MW):\n\n"
                f"• **Total Estimated CapEx:** ₹ {cost.get('total_project_cost_cr', '—')} Cr\n"
                f"• Civil Works (Dam, Tunnel, Powerhouse): ₹ {cost.get('civil_cost_cr', '—')} Cr\n"
                f"• Electro-Mechanical Equipment (Turbines, GIS): ₹ {cost.get('equipment_cost_cr', '—')} Cr\n"
                f"• Other Costs & Normalization adjustments: ₹ {cost.get('other_cost_cr', '—')} Cr\n"
                f"• Cost Normalized (to 2024 index): ₹ {cost.get('cost_normalized_2024_cr', '—')} Cr\n\n"
                f"This cost prediction was computed using a Gradient Boosting algorithm trained on similar historical CEA DPR and CAG audit datasets."
            )
        elif monitoring_context:
            status = monitoring_context.get("status", {}) or {}
            pid = monitoring_context.get("project_id")
            name = monitoring_context.get("project_name", "Monitored Plant")
            return (
                f"📊 Capital Cost & Budget Monitoring for Project {pid} ({name}):\n\n"
                f"• **Project Name:** {name}\n"
                f"• **Overall Cost Status:** The cost details and normalized curves are available in the CapEx Breakdown panel.\n"
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

    # ─── 2. Material BOQ & Concrete Queries ──────────────────────────────────
    if any(k in query for k in ["concrete", "cement", "steel", "boq", "rebar", "intensity", "material", "quantity"]):
        if estimation_result:
            mats = estimation_result.get("model_1_materials", {}) or {}
            return (
                f"🧱 Predicted Material Bill of Quantities (BOQ):\n\n"
                f"• **Concrete Volume:** {mats.get('concrete_m3', '—'):,} m³ (dam, powerhouse, tunnels)\n"
                f"• **Cement Quantity:** {mats.get('cement_mt', '—'):,} MT (standard OPC 43/53 grade)\n"
                f"• **Reinforcement Steel (Rebar):** {mats.get('rebar_steel_mt', '—'):,} MT (Fe 500D TMT)\n"
                f"• **Penstock Steel (High Strength):** {mats.get('penstock_steel_mt', '—'):,} MT\n\n"
                f"Predicted by XGBoost MultiOutput models using historical PARIVESH environment clearances and NHPC commercial tenders."
            )
        elif monitoring_context:
            mats = monitoring_context.get("materials", {}) or {}
            shortages = mats.get("shortage_count") or 0
            return (
                f"🧱 Material Stock & Availability Status:\n\n"
                f"• **Critical Stock Alerts:** {shortages} safety stock threshold breaches detected.\n"
                f"• **Detailed Materials list:** Available on the Material Availability dashboard metrics.\n"
                f"• **Procurement Status:** Procurement orders are listed in the logs panel below."
            )
        else:
            return (
                "🧱 Construction Material BOQ Benchmarks (per MW Installed Capacity):\n\n"
                "• Concrete Volume: 2,500 – 4,200 m³ / MW (M25–M40 grade for dam & powerhouse structures).\n"
                "• Cement Quantity: 700 – 1,200 MT / MW (OPC 43/53 grade).\n"
                "• Reinforcement Steel (Rebar Fe500D): 180 – 320 MT / MW.\n"
                "• Penstock Steel (High Tensile Grade E350): 25 – 60 MT / MW depending on static head pressure."
            )

    # ─── 3. Project Delay & Monitoring Status ────────────────────────────────
    if any(k in query for k in ["delay", "status", "progress", "schedule", "actual", "overrun", "monitoring"]):
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
        elif estimation_result:
            dur = estimation_result.get("model_4_duration", {}) or {}
            return (
                f"⏱️ Predicted Construction Duration:\n\n"
                f"• **Construction Duration:** {dur.get('construction_duration_months', '—')} Months ({dur.get('estimated_years', '—')} years)\n\n"
                f"Estimated by Gradient Boosting models based on geographic elevation, terrain complexity, and structural sizing parameters."
            )
        else:
            return (
                "⏱️ Hydroelectric Schedule Monitoring & Delay Management:\n\n"
                "Typically, large projects average 60–90 months construction time in India. "
                "Main root causes for delay include geological surprises (tunneling), land acquisition issues, "
                "and seasonal monsoons/flood risks."
            )

    # ─── 4. Generation & Capacity Factor ─────────────────────────────────────
    if any(k in query for k in ["generation", "power", "gwh", "energy", "efficiency", "hydrology"]):
        if estimation_result:
            inputs = estimation_result.get("project_inputs", {}) or {}
            gen = estimation_result.get("model_2_generation", {}) or {}
            return (
                f"⚡ Predicted Power Generation details for {inputs.get('capacity_mw')} MW project:\n\n"
                f"• **Annual Energy Generation:** {gen.get('annual_generation_gwh', '—')} GWh\n"
                f"• **Estimated Capacity Factor (PLF):** {gen.get('capacity_factor_pct', '—')}%\n"
                f"• **Design Discharge:** {inputs.get('design_flow_m3s', '—')} m³/s at {inputs.get('net_head_m', '—')} m net head\n"
                f"• **Turbine Choice:** {inputs.get('turbine_type')} Turbine ({inputs.get('number_of_units')} units)\n\n"
                f"Generation estimates are based on a 90% dependable hydrology year profile with typical efficiency metrics."
            )
        else:
            return (
                "⚙️ Turbine Design & Flow Mechanics:\n\n"
                "• **Francis Turbine:** Ideal for Medium Head (40m - 350m).\n"
                "• **Pelton Turbine:** Ideal for High Head (>200m), lower discharge flow.\n"
                "• **Kaplan Turbine:** Ideal for Low Head (<50m), high discharge flow.\n"
                "• Power Equation: Power (kW) = 9.81 * Flow (m³/s) * Head (m) * Efficiency (η)."
            )

    # ─── 5. Basin & River Geography ──────────────────────────────────────────
    if any(k in query for k in ["basin", "river", "ganga", "sutlej", "indus", "siang", "periyar", "krishna", "godavari", "location"]):
        return (
            "🌊 Hydroelectric River Basin Regimes (Indian Context):\n\n"
            "• Primary Active Basins in ConstructIQ Dataset:\n"
            "  1. Ganga River Basin (Uttarakhand / UP): High head run-of-river & storage projects (Tehri, Alaknanda, Bhagirathi).\n"
            "  2. Sutlej / Indus Basin (Himachal / J&K): High discharge glacial rivers (Nathpa Jhakri, Chenab, Beas).\n"
            "  3. Brahmaputra / Siang Basin (Arunachal / Assam): Ultra-large capacity projects (Subansiri, Siang Upper).\n"
            "  4. Periyar & Peninsular Basins (Kerala, AP, Karnataka): Medium head reservoir powerhouses (Idukki, Srisailam)."
        )

    # ─── 6. CEA / DPR Submission Norms ───────────────────────────────────────
    if "cea" in query or "dpr" in query or "statutory" in query:
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

    # ─── 7. PARIVESH / Environmental Clearances ──────────────────────────────
    if "parivesh" in query or "environmental" in query or "clearance" in query or "moefcc" in query:
        return (
            "🍃 PARIVESH (MoEFCC) Environmental & Forest Clearance Norms:\n\n"
            "• Category A (>50 MW): Requires Central MoEFCC Expert Appraisal Committee (EAC) approval.\n"
            "• Key Clearances:\n"
            "  1. Environmental Clearance (EC): EIA & EMP report approval.\n"
            "  2. Forest Clearance (FC): Forest diversion approval under Forest Conservation Act.\n"
            "  3. E-Flow Release: Minimum 15–20% lean season river flow maintenance."
        )

    # ─── 8. Welcome / Default Answer ─────────────────────────────────────────
    return (
        "🌊 ConstructIQ Hydro Specialist AI Assistant:\n\n"
        "I can help you with hydroelectric power calculations, turbine selection (Francis, Pelton, Kaplan), "
        "material BOQ benchmarks (Concrete, Rebar, Penstocks), CapEx costs (₹ Cr/MW), "
        "river basin regimes (Ganga, Sutlej, Subansiri), and statutory guidelines (CEA DPR, PARIVESH)."
    )

