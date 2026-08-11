# -*- coding: utf-8 -*-
"""
ConstructIQ — Hydro Power Specialist Conversational Chatbot Engine.
Integrates Groq LLM (LLaMA-3.3-70B / LLaMA3-8B) with domain-specific hydro engineering context,
CEA/PARIVESH regulatory norms, and intelligent domain fallback.
"""

import os
import requests
from typing import List, Dict

SYSTEM_PROMPT = """You are ConstructIQ's Senior Hydro Power Specialist & Engineering AI Assistant.
You specialize in hydroelectric power project estimation, hydraulic design physics, material BOQ (Concrete, Steel, Penstocks), project costing (₹ Cr/MW), construction schedules, and Indian statutory regulatory guidelines (CEA DPRs, MoEFCC PARIVESH clearances, CPPP tenders, CAG audits).

Key Technical & Statutory Knowledge Base:
1. Hydraulic Power Physics: Power (kW) = 9.81 * Q (m³/s) * H_net (m) * Efficiency (η ~ 0.88–0.92).
2. Turbine Selection Rules:
   - Pelton: High Head (>200m), low flow.
   - Francis: Medium Head (40m - 350m), medium to high flow.
   - Kaplan/Propeller: Low Head (<50m), high discharge flow.
   - Cross-Flow/Kaplan: Mini/Micro Hydro (<25 MW).
3. Material BOQ Benchmarks (Indian Himalayan & Peninsular Conditions):
   - Concrete Volume: 2,500 – 4,200 m³ / MW.
   - Cement Quantity: 700 – 1,200 MT / MW.
   - Reinforcement Steel (Rebar): 180 – 320 MT / MW.
   - Penstock Steel: Grade IS 2062 / E350, 25 – 60 MT / MW depending on pressure head.
4. Financial Costs & Schedule Benchmarks:
   - Hydro Project Capital Cost: ₹ 8.5 Cr – ₹ 14.5 Cr / MW (Civil ~60–65%, Electro-Mechanical ~35–40%).
   - Construction Duration: 60 – 90 months for Large/Medium, 24 – 48 months for Small Hydro.
5. Government Statutory Authorities:
   - CEA (Central Electricity Authority): DPR technical appraisal & grid coupling.
   - PARIVESH (MoEFCC): Environmental Clearance (EC), Forest Clearance (FC), EIA/EMP reports.
   - CPPP (etenders.gov.in): Central public procurement BOQ contracts & tender schedules.

Guidelines:
- Give direct, professional, expert answers formatted clearly.
- Keep answers concise, informative, and focused on hydro power plant engineering and project management.
- Always use professional engineering terminology and clear currency notation (₹ Cr / MW).
"""

def generate_chat_response(messages: List[Dict[str, str]]) -> str:
    """
    Sends conversation history to Groq API (or returns intelligent domain fallback if API key is not configured).
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    # If Groq API key is present and valid, call Groq LLaMA-3.3 LLM
    if api_key and (api_key.startswith("gsk_") or len(api_key) > 20):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in messages:
                role = "user" if msg.get("role") in ("user", "human") else "assistant"
                formatted_messages.append({"role": role, "content": msg.get("content", "")})

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": formatted_messages,
                "temperature": 0.3,
                "max_tokens": 800,
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"[WARN] Groq API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[WARN] Groq API exception: {e}. Falling back to domain engine.")

    # Extract latest user message for intelligent rule fallback
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") in ("user", "human"):
            last_user_msg = msg.get("content", "").lower()
            break

    return _domain_fallback_answer(last_user_msg)


def _domain_fallback_answer(query: str) -> str:
    """Intelligent multi-branch domain knowledge engine for hydro inquiries."""
    
    # 1. Francis Turbine specific query
    if "francis" in query:
        return (
            "⚙️ Francis Turbine Flow & Design Calculation:\n\n"
            "• Applicable Head Range: Medium Head (40 m to 350 m).\n"
            "• Discharge Flow Formula: Q = P / (9.81 × H_net × η_turbine × η_generator).\n"
            "• For a Francis turbine operating at 88% overall efficiency with H_net = 120m and P = 45 MW:\n"
            "  Q = 45,000 / (9.81 × 120 × 0.88) ≈ 43.5 m³/s.\n"
            "• Key Advantage: Best peak-to-part-load efficiency profile for mixed river regimes."
        )

    # 2. CEA DPR Submission Norms
    if "cea" in query or "dpr" in query:
        return (
            "🏛️ CEA DPR Submission & Technical Appraisal Guidelines:\n\n"
            "• Applicability: Required for all Hydro Projects with Capital Outlay > ₹ 1,000 Cr under Section 8 of Electricity Act 2003.\n"
            "• Key Chapter Requirements:\n"
            "  1. Hydrology & Power Potential: 90% dependable year energy generation calculations.\n"
            "  2. Geological & Geotechnical Studies: Tunneling Q-system ratings & 3D seismic profiling.\n"
            "  3. Civil Structural Layout: Spillway design flood (PMF), Dam stability analysis.\n"
            "  4. Electro-Mechanical Specs: Turbine/Generator unit ratings, switchyard GIS layout.\n"
            "  5. Cost Estimates & Financial Viability: Tarif calculation per kWh & levelized cost of energy (LCOE)."
        )

    # 3. PARIVESH / Environmental Clearance
    if "parivesh" in query or "environmental" in query or "moefcc" in query:
        return (
            "🍃 PARIVESH (MoEFCC) Environmental Clearance (EC) Guidelines:\n\n"
            "• Category A Projects (>50 MW or border/forest zones): Central MoEFCC EAC approval required.\n"
            "• Category B Projects (<50 MW): State Level SEIAA clearance.\n"
            "• Mandatory Submissions:\n"
            "  1. EIA (Environmental Impact Assessment) & EMP (Environment Management Plan).\n"
            "  2. Environmental Flow (E-Flow) release: Minimum 15–20% of lean season natural river flow.\n"
            "  3. Catchment Area Treatment (CAT) Plan & Compensatory Afforestation (CA)."
        )

    # 4. General Hydro Power Equation
    if any(k in query for k in ["power", "formula", "equation", "calculate power"]):
        return (
            "⚡ Hydroelectric Power Generation Equation:\n\n"
            "• Primary Equation: P (kW) = 9.81 × Q (m³/s) × H_net (m) × η\n"
            "• Where:\n"
            "  - P = Generated Power output in kilowatts (kW)\n"
            "  - Q = Design water flow rate in m³/s\n"
            "  - H_net = Net hydraulic head in meters (Gross head minus tunnel friction losses)\n"
            "  - η = Combined turbine-generator efficiency (~0.88 – 0.92)"
        )

    # 5. General Turbine Selection
    if "turbine" in query or "pelton" in query or "kaplan" in query:
        return (
            "⚙️ Turbine Selection Guidelines:\n\n"
            "1. Pelton (Impulse): High Head (>200m) with low flow rates.\n"
            "2. Francis (Reaction): Medium Head (40m – 350m) with medium/high flows.\n"
            "3. Kaplan (Axial Reaction): Low Head (<50m) with high variable flow rates.\n"
            "4. Cross-Flow / Bulb: Compact surface installations for Mini & Micro Hydro (<25 MW)."
        )

    # 6. Cost & Financial Benchmarks
    if any(k in query for k in ["cost", "budget", "price", "crore", "cr", "capex"]):
        return (
            "💰 Hydro Project Financial & Cost Benchmarks:\n\n"
            "• Total CapEx Benchmark: ₹ 8.5 Cr to ₹ 14.5 Cr per MW installed capacity.\n"
            "• Cost Allocation:\n"
            "  - Civil Works (Dam, Tunnel, Powerhouse): 60% – 65% of total outlay.\n"
            "  - Electro-Mechanical Equipment (Turbines, Generators): 35% – 40%.\n"
            "• Major Drivers: Headrace tunnel rock geology, dam excavation depth, and penstock pressure rating."
        )

    # 7. Material Quantities & BOQ
    if any(k in query for k in ["concrete", "cement", "steel", "material", "boq", "rebar"]):
        return (
            "🧱 Material BOQ Construction Benchmarks (per MW):\n\n"
            "• Concrete Volume: 2,500 – 4,200 m³ / MW.\n"
            "• Cement Quantity: 700 – 1,200 MT / MW.\n"
            "• Reinforcement Steel (Rebar Fe500D): 180 – 320 MT / MW.\n"
            "• Penstock Steel (Grade E350): 25 – 60 MT / MW."
        )

    # 8. Timeline & Duration
    if any(k in query for k in ["duration", "timeline", "months", "years", "schedule"]):
        return (
            "⏱️ Construction Duration Benchmarks:\n\n"
            "• Large Hydro (>100 MW): 60 to 84 months (5 to 7 years).\n"
            "• Medium Hydro (25–100 MW): 42 to 60 months (3.5 to 5 years).\n"
            "• Small Hydro (<25 MW): 24 to 36 months (2 to 3 years)."
        )

    # Default fallback welcome text
    return (
        "🌊 ConstructIQ Hydro Engineering Specialist Assistant:\n\n"
        "I can help you with hydroelectric power calculations, turbine selection (Francis, Pelton, Kaplan), "
        "material BOQ benchmarks (Concrete, Rebar, Penstocks), CapEx cost estimates (₹ Cr/MW), "
        "and statutory clearance norms (CEA DPR, PARIVESH MoEFCC).\n\n"
        "Ask any question regarding hydro plant estimation or construction!"
    )
