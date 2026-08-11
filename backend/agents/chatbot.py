# -*- coding: utf-8 -*-
"""
ConstructIQ — Hydro Power Specialist Conversational Chatbot Engine.
Integrates Groq LLM (LLaMA-3.3 / LLaMA3-8B) with domain-specific hydro engineering context,
CEA/PARIVESH regulatory norms, and instant domain intelligence fallback.
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
    Sends conversation history to Groq API (or returns domain fallback instantly if API key is not configured).
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    # Fast validation: if key is absent or placeholder, use instant domain fallback (<0.01s)
    if not api_key or not api_key.startswith("gsk_"):
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") in ("user", "human"):
                last_user_msg = msg.get("content", "").lower()
                break
        return _domain_fallback_answer(last_user_msg)

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
            "max_tokens": 600,
        }

        # Fast 2.5s timeout to prevent UI freezes
        resp = requests.post(url, json=payload, headers=headers, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[WARN] Groq API call timeout/error: {e}. Using instant domain response.")

    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") in ("user", "human"):
            last_user_msg = msg.get("content", "").lower()
            break
    return _domain_fallback_answer(last_user_msg)


def _domain_fallback_answer(query: str) -> str:
    """Rule-based domain intelligence engine for hydro inquiries."""
    if any(k in query for k in ["head", "flow", "power", "formula", "capacity", "mw"]):
        return (
            "⚡ Hydroelectric Power Calculation & Hydraulic Parameters:\n\n"
            "• Power Equation: P (kW) = 9.81 × Q (m³/s) × H_net (m) × η (efficiency ~ 0.90).\n"
            "• Capacity Norms: Installed capacity (MW) is derived from peak design flow and net hydraulic head.\n"
            "• Head Loss Factor: Net head is typically 92–95% of gross head after friction losses in headrace tunnels & penstocks."
        )

    if any(k in query for k in ["turbine", "francis", "pelton", "kaplan"]):
        return (
            "⚙️ Turbine Selection Guidelines for Hydro Plants:\n\n"
            "1. Francis Turbine: Ideal for Medium Head (40m – 350m). Most widely used in Himalayan & Peninsular projects.\n"
            "2. Pelton Turbine: Selected for High Head (>200m) with lower discharge flow rates.\n"
            "3. Kaplan Turbine: Ideal for Low Head (<50m) and high variable discharge flows.\n"
            "4. Cross-Flow / Bulb: Suitable for Mini and Micro hydro installations (<25 MW)."
        )

    if any(k in query for k in ["cost", "budget", "price", "crore", "cr", "mw"]):
        return (
            "💰 Hydro Power Cost & Financial Benchmarking (Indian Context):\n\n"
            "• Average Benchmark: ₹ 8.5 Cr to ₹ 14.5 Cr per MW installed capacity.\n"
            "• Civil Works: Accounts for 60% – 65% of total project capital outlay (dams, tunnels, surge shafts).\n"
            "• Electro-Mechanical (E&M): Accounts for 35% – 40% (turbines, generators, transformers, switchyards).\n"
            "• Escalation Drivers: Tunneling rock geology, land acquisition, and environmental mitigation."
        )

    if any(k in query for k in ["concrete", "cement", "steel", "material", "boq", "rebar"]):
        return (
            "🧱 Material Quantity (BOQ) Benchmarks:\n\n"
            "• Concrete Volume: 2,500 – 4,200 m³ / MW.\n"
            "• Cement Quantity: 700 – 1,200 MT / MW.\n"
            "• Reinforcement Steel (Rebar): 180 – 320 MT / MW (Fe500D grade).\n"
            "• Penstock Steel: 25 – 60 MT / MW (high tensile IS 2062 / E350 steel plates)."
        )

    if any(k in query for k in ["cea", "parivesh", "dpr", "government", "clearance", "cag", "e-procurement"]):
        return (
            "🏛️ Statutory & Government Regulatory Framework:\n\n"
            "• CEA (Central Electricity Authority): Techno-economic clearance for DPRs > ₹ 1,000 Cr.\n"
            "• PARIVESH (MoEFCC): Mandatory Environmental Clearance (EC) & Forest Clearance (FC).\n"
            "• CPPP / eTenders (etenders.gov.in): Official BOQ schedules and tender itemization.\n"
            "• CAG Audits: Historical time/cost overrun benchmarks for risk mitigation."
        )

    return (
        "🌊 ConstructIQ Hydro Specialist AI Assistant:\n\n"
        "I can answer questions regarding hydro power plant estimations, material BOQ (concrete/steel), "
        "cost per MW, turbine selection, construction schedules, and statutory government requirements (CEA, PARIVESH).\n\n"
        "Feel free to ask about specific plant parameters or estimation benchmarks!"
    )
