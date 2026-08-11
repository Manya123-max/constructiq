# -*- coding: utf-8 -*-
"""
ConstructIQ — Hydro Power Specialist Conversational Chatbot Engine.
Integrates Groq LLM (LLaMA-3.3-70B / LLaMA-3.1-8B) with domain-specific hydro engineering context,
CEA/PARIVESH regulatory norms, and robust multi-model fallback.
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

def generate_chat_response(messages: List[Dict[str, str]]) -> str:
    """
    Sends conversation history to Groq API with robust model fallback, or returns domain engine answer.
    Never raises an unhandled exception to client.
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    if api_key and (api_key.startswith("gsk_") or len(api_key) > 20):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            role = "user" if msg.get("role") in ("user", "human") else "assistant"
            formatted_messages.append({"role": role, "content": msg.get("content", "")})

        # Try Groq models in sequence for maximum reliability
        for model_name in GROQ_MODELS:
            try:
                payload = {
                    "model": model_name,
                    "messages": formatted_messages,
                    "temperature": 0.3,
                    "max_tokens": 800,
                }

                resp = requests.post(url, json=payload, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f"[WARN] Groq model {model_name} returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[WARN] Exception calling Groq model {model_name}: {e}")

    # Fallback to intelligent rule-based domain engine if Groq is unavailable
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") in ("user", "human"):
            last_user_msg = msg.get("content", "").lower()
            break

    return _domain_fallback_answer(last_user_msg)


def _domain_fallback_answer(query: str) -> str:
    """Intelligent multi-branch domain knowledge engine for hydro inquiries."""
    
    if "francis" in query or "flow" in query or "turbine" in query:
        return (
            "⚙️ Francis Turbine Flow & Design Calculation:\n\n"
            "• Applicable Head Range: Medium Head (40 m to 350 m).\n"
            "• Discharge Flow Formula: Q = P / (9.81 × H_net × η_turbine × η_generator).\n"
            "• Example (45 MW Plant, H_net = 120m, 88% Efficiency):\n"
            "  Q = 45,000 / (9.81 × 120 × 0.88) ≈ 43.5 m³/s.\n"
            "• Key Advantage: Superior part-load efficiency profile for variable seasonal flows."
        )

    if "cea" in query or "dpr" in query:
        return (
            "🏛️ CEA DPR Submission & Technical Appraisal Guidelines:\n\n"
            "• Applicability: Required for Hydro Projects > ₹ 1,000 Cr under Section 8 of Electricity Act 2003.\n"
            "• Chapter Requirements:\n"
            "  1. Hydrology & Power Potential: 90% dependable year energy calculations.\n"
            "  2. Geotechnical & Geological Studies: Tunneling Q-system ratings.\n"
            "  3. Civil Structural Layout: PMF spillway flood routing.\n"
            "  4. Electro-Mechanical Specs: Turbine/Generator unit ratings.\n"
            "  5. Financial Viability: Levelized Tariff per kWh."
        )

    if "parivesh" in query or "environmental" in query:
        return (
            "🍃 PARIVESH (MoEFCC) Environmental Clearance (EC) Guidelines:\n\n"
            "• Category A Projects (>50 MW): Central MoEFCC EAC approval.\n"
            "• Mandatory Submissions:\n"
            "  1. EIA & EMP Reports.\n"
            "  2. Environmental Flow (E-Flow): Minimum 15–20% lean season flow release.\n"
            "  3. Catchment Area Treatment (CAT) & Compensatory Afforestation."
        )

    if any(k in query for k in ["power", "formula", "capacity", "mw"]):
        return (
            "⚡ Hydroelectric Power Equation:\n\n"
            "• P (kW) = 9.81 × Q (m³/s) × H_net (m) × η\n"
            "• P = Generated Power output in kW\n"
            "• Q = Design flow rate in m³/s\n"
            "• H_net = Net hydraulic head in meters\n"
            "• η = Turbine-generator efficiency (~0.90)"
        )

    if any(k in query for k in ["cost", "budget", "price", "cr"]):
        return (
            "💰 Hydro Financial Benchmarks:\n\n"
            "• Average CapEx: ₹ 8.5 Cr to ₹ 14.5 Cr per MW.\n"
            "• Breakdown: Civil Works (~65%), Electro-Mechanical (~35%)."
        )

    return (
        "🌊 ConstructIQ Hydro Specialist AI Assistant:\n\n"
        "Ask me anything about hydro power plant estimations, turbine selection (Francis, Pelton, Kaplan), "
        "material BOQs, CapEx costs (₹ Cr/MW), and statutory guidelines (CEA DPR, PARIVESH)."
    )
