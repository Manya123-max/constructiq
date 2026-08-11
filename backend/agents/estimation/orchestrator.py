# -*- coding: utf-8 -*-
"""
ConstructIQ - 4-Model Estimation Orchestration Pipeline.
Chains execution across:
1. Model 1 — Material Estimation Model (Concrete, Cement, Rebar, Structural Steel, Penstock Steel, Aggregate, Sand, Excavation)
2. Model 2 — Power Generation Model (Annual GWh & Capacity Factor)
3. Model 3 — Cost Model (Civil, Equipment & Total Cost using Material Estimates)
4. Model 4 — Construction Duration Model (Duration Months using Dam/Tunnel/Concrete Parameters)
5. RAG Retrieval & Confidence Score Engine (70–90% Confidence + Traceable Government Sources)
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_DIR = os.path.join(BASE_DIR, "ml", "models")
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
sys.path.insert(0, BASE_DIR)

from rag.vector_store import search_similar_projects, calculate_confidence_score, get_government_citations

_model_cache = {}

def load_ml_models():
    global _model_cache
    if not _model_cache:
        _model_cache['mat_model'] = joblib.load(os.path.join(MODEL_DIR, "hydro_material_model.joblib"))
        _model_cache['gen_model'] = joblib.load(os.path.join(MODEL_DIR, "hydro_generation_model.joblib"))
        _model_cache['cost_model'] = joblib.load(os.path.join(MODEL_DIR, "hydro_cost_model.joblib"))
        _model_cache['dur_model'] = joblib.load(os.path.join(MODEL_DIR, "hydro_duration_model.joblib"))
        _model_cache['encoders'] = joblib.load(os.path.join(MODEL_DIR, "hydro_encoders.joblib"))
    return _model_cache

def encode_categorical_value(col_name: str, val: str, encoders: dict) -> float:
    if col_name in encoders:
        enc = encoders[col_name]
        try:
            val_df = pd.DataFrame([[str(val)]], columns=[col_name])
            encoded_val = enc.transform(val_df)[0][0]
            return float(encoded_val)
        except Exception:
            return 0.0
    return 0.0

def run_estimation_pipeline(input_data: Dict[str, Any]) -> Dict[str, Any]:
    models = load_ml_models()
    mat_model = models['mat_model']
    gen_model = models['gen_model']
    cost_model = models['cost_model']
    dur_model = models['dur_model']
    encoders = models['encoders']

    # 1. Parse Project Input Data
    cap_mw = float(input_data.get("capacity_mw", 250.0))
    num_units = int(input_data.get("number_of_units", 4))
    unit_cap_mw = cap_mw / num_units
    gross_head = float(input_data.get("gross_head_m", 180.0))
    net_head = float(input_data.get("net_head_m", gross_head * 0.95))
    
    # Calculate hydraulic design flow if missing: P = rho * g * Q * H * eta / 1e6
    if "design_flow_m3s" in input_data and float(input_data["design_flow_m3s"]) > 0:
        design_flow = float(input_data["design_flow_m3s"])
    else:
        design_flow = round((cap_mw * 1e6) / (1000.0 * 9.81 * net_head * 0.90), 2)

    dam_height = float(input_data.get("dam_height_m", 65.0))
    dam_length = float(input_data.get("dam_length_m", dam_height * 4.0))
    tunnel_len_km = float(input_data.get("tunnel_length_km", 8.5))
    tunnel_dia_m = float(input_data.get("tunnel_diameter_m", 6.5))
    penstock_len_m = float(input_data.get("penstock_length_m", 450.0))
    penstock_dia_m = float(input_data.get("penstock_diameter_m", 3.8))
    reservoir_vol_mcm = float(input_data.get("reservoir_volume_mcm", 120.0))
    catchment_area_km2 = float(input_data.get("catchment_area_km2", 1800.0))
    elevation_m = float(input_data.get("elevation_m", 1400.0))
    state = str(input_data.get("state", "Uttarakhand"))
    project_type = str(input_data.get("project_type", "run-of-river"))

    # Turbine type selection rules
    if net_head > 250.0:
        turbine_type = "Pelton"
    elif net_head > 45.0:
        turbine_type = "Francis"
    else:
        turbine_type = "Kaplan" if cap_mw > 0.1 else "Cross-flow"

    dam_type = str(input_data.get("dam_type", "Concrete Gravity"))
    powerhouse_type = str(input_data.get("powerhouse_type", "Underground" if cap_mw > 100 else "Surface"))
    terrain_type = str(input_data.get("terrain_type", "Mountainous"))

    # Excavation volume estimation if not supplied
    if "excavation_volume_m3" in input_data and float(input_data["excavation_volume_m3"]) > 0:
        excavation_vol_m3 = float(input_data["excavation_volume_m3"])
    else:
        excavation_vol_m3 = (cap_mw * 4500.0) + (tunnel_len_km * 180000.0) + (dam_height * 12000.0)

    terrain_comp = float(input_data.get("terrain_complexity_score", 3.5))
    civil_comp = float(input_data.get("civil_complexity_score", 3.8))
    hydro_comp = float(input_data.get("hydro_complexity_score", 3.6))

    # ─── MODEL 1: Material Estimation Model ─────────────────────────────────
    mat_feature_cols = [
        "capacity_mw", "number_of_units", "gross_head_m", "net_head_m", "design_flow_m3s",
        "dam_height_m", "dam_length_m", "penstock_length_m", "penstock_diameter_m",
        "tunnel_length_km", "tunnel_diameter_m", "reservoir_volume_mcm", "catchment_area_km2",
        "elevation_m", "excavation_volume_m3", "terrain_complexity_score",
        "civil_complexity_score", "hydro_complexity_score",
        "project_type", "turbine_type", "dam_type", "powerhouse_type", "terrain_type", "state"
    ]
    mat_input_dict = {
        "capacity_mw": cap_mw, "number_of_units": num_units, "gross_head_m": gross_head,
        "net_head_m": net_head, "design_flow_m3s": design_flow, "dam_height_m": dam_height,
        "dam_length_m": dam_length, "penstock_length_m": penstock_len_m, "penstock_diameter_m": penstock_dia_m,
        "tunnel_length_km": tunnel_len_km, "tunnel_diameter_m": tunnel_dia_m, "reservoir_volume_mcm": reservoir_vol_mcm,
        "catchment_area_km2": catchment_area_km2, "elevation_m": elevation_m, "excavation_volume_m3": excavation_vol_m3,
        "terrain_complexity_score": terrain_comp, "civil_complexity_score": civil_comp, "hydro_complexity_score": hydro_comp,
        "project_type": encode_categorical_value("project_type", project_type, encoders),
        "turbine_type": encode_categorical_value("turbine_type", turbine_type, encoders),
        "dam_type": encode_categorical_value("dam_type", dam_type, encoders),
        "powerhouse_type": encode_categorical_value("powerhouse_type", powerhouse_type, encoders),
        "terrain_type": encode_categorical_value("terrain_type", terrain_type, encoders),
        "state": encode_categorical_value("state", state, encoders),
    }
    df_mat_input = pd.DataFrame([mat_input_dict])[mat_feature_cols]
    pred_mat_raw = mat_model.predict(df_mat_input)[0]

    materials_predicted = {
        "concrete_m3": round(max(10.0, pred_mat_raw[0]), 1),
        "cement_mt": round(max(3.0, pred_mat_raw[1]), 1),
        "reinforcement_steel_mt": round(max(1.0, pred_mat_raw[2]), 1),
        "structural_steel_mt": round(max(0.5, pred_mat_raw[3]), 1),
        "penstock_steel_mt": round(max(0.2, pred_mat_raw[4]), 1),
        "aggregate_m3": round(max(8.0, pred_mat_raw[5]), 1),
        "sand_m3": round(max(4.0, pred_mat_raw[6]), 1),
        "excavation_m3": round(max(50.0, pred_mat_raw[7]), 1),
    }

    # Intensity Metrics (Derived for Validation / Display)
    material_intensities = {
        "concrete_m3_per_mw": round(materials_predicted["concrete_m3"] / cap_mw, 2),
        "cement_mt_per_mw": round(materials_predicted["cement_mt"] / cap_mw, 2),
        "reinforcement_steel_mt_per_mw": round(materials_predicted["reinforcement_steel_mt"] / cap_mw, 2),
        "structural_steel_mt_per_mw": round(materials_predicted["structural_steel_mt"] / cap_mw, 2),
        "penstock_steel_mt_per_mw": round(materials_predicted["penstock_steel_mt"] / cap_mw, 2),
        "excavation_m3_per_mw": round(materials_predicted["excavation_m3"] / cap_mw, 2),
    }

    # ─── MODEL 2: Power Generation Model ────────────────────────────────────
    gen_feature_cols = [
        "capacity_mw", "number_of_units", "gross_head_m", "net_head_m", "design_flow_m3s",
        "annual_inflow_mcm", "reservoir_volume_mcm", "catchment_area_km2",
        "turbine_efficiency", "generator_efficiency", "design_efficiency", "availability_factor",
        "project_type", "turbine_type", "state"
    ]
    annual_inflow = float(input_data.get("annual_inflow_mcm", design_flow * 31.536 * 0.8))
    gen_input_dict = {
        "capacity_mw": cap_mw, "number_of_units": num_units, "gross_head_m": gross_head,
        "net_head_m": net_head, "design_flow_m3s": design_flow, "annual_inflow_mcm": annual_inflow,
        "reservoir_volume_mcm": reservoir_vol_mcm, "catchment_area_km2": catchment_area_km2,
        "turbine_efficiency": 0.93, "generator_efficiency": 0.97, "design_efficiency": 0.902, "availability_factor": 0.92,
        "project_type": encode_categorical_value("project_type", project_type, encoders),
        "turbine_type": encode_categorical_value("turbine_type", turbine_type, encoders),
        "state": encode_categorical_value("state", state, encoders),
    }
    df_gen_input = pd.DataFrame([gen_input_dict])[gen_feature_cols]
    pred_gen_gwh = float(gen_model.predict(df_gen_input)[0])
    pred_gen_gwh = round(max(0.1, pred_gen_gwh), 2)
    implied_capacity_factor = round((pred_gen_gwh * 1000.0) / (cap_mw * 8760.0), 4)
    implied_capacity_factor_pct = round(implied_capacity_factor * 100.0, 2)

    # ─── MODEL 3: Project Cost Model ────────────────────────────────────────
    cost_feature_cols = [
        "capacity_mw", "number_of_units", "net_head_m", "dam_height_m", "tunnel_length_km",
        "penstock_length_m", "project_type", "turbine_type", "state", "commissioning_year",
        "concrete_m3", "cement_mt", "reinforcement_steel_mt", "structural_steel_mt",
        "penstock_steel_mt", "aggregate_m3", "sand_m3", "excavation_m3"
    ]
    cost_input_dict = {
        "capacity_mw": cap_mw, "number_of_units": num_units, "net_head_m": net_head,
        "dam_height_m": dam_height, "tunnel_length_km": tunnel_len_km, "penstock_length_m": penstock_len_m,
        "project_type": encode_categorical_value("project_type", project_type, encoders),
        "turbine_type": encode_categorical_value("turbine_type", turbine_type, encoders),
        "state": encode_categorical_value("state", state, encoders),
        "commissioning_year": int(input_data.get("commissioning_year", 2024)),
        **materials_predicted
    }
    df_cost_input = pd.DataFrame([cost_input_dict])[cost_feature_cols]
    pred_cost_raw = cost_model.predict(df_cost_input)[0]

    cost_predicted = {
        "civil_cost_cr": round(max(0.1, pred_cost_raw[0]), 2),
        "equipment_cost_cr": round(max(0.1, pred_cost_raw[1]), 2),
        "total_project_cost_cr": round(max(0.2, pred_cost_raw[2]), 2),
        "cost_per_mw_cr": round(pred_cost_raw[2] / cap_mw, 2),
    }

    # ─── MODEL 4: Construction Duration Model ───────────────────────────────
    dur_feature_cols = [
        "capacity_mw", "number_of_units", "dam_height_m", "dam_length_m", "tunnel_length_km",
        "tunnel_diameter_m", "penstock_length_m", "excavation_volume_m3", "concrete_m3",
        "terrain_complexity_score", "civil_complexity_score", "hydro_complexity_score",
        "project_type", "dam_type", "powerhouse_type", "state"
    ]
    dur_input_dict = {
        "capacity_mw": cap_mw, "number_of_units": num_units, "dam_height_m": dam_height,
        "dam_length_m": dam_length, "tunnel_length_km": tunnel_len_km, "tunnel_diameter_m": tunnel_dia_m,
        "penstock_length_m": penstock_len_m, "excavation_volume_m3": excavation_vol_m3,
        "concrete_m3": materials_predicted["concrete_m3"],
        "terrain_complexity_score": terrain_comp, "civil_complexity_score": civil_comp, "hydro_complexity_score": hydro_comp,
        "project_type": encode_categorical_value("project_type", project_type, encoders),
        "dam_type": encode_categorical_value("dam_type", dam_type, encoders),
        "powerhouse_type": encode_categorical_value("powerhouse_type", powerhouse_type, encoders),
        "state": encode_categorical_value("state", state, encoders),
    }
    df_dur_input = pd.DataFrame([dur_input_dict])[dur_feature_cols]
    pred_dur_months = float(dur_model.predict(df_dur_input)[0])
    pred_dur_months = round(max(3.0, min(120.0, pred_dur_months)), 1)

    # ─── RAG & Confidence Score Calculation ─────────────────────────────────
    similar_projs = search_similar_projects(cap_mw, net_head, state, n_results=5)
    confidence_data = calculate_confidence_score(cap_mw, net_head, similar_projs)

    return {
        "status": "success",
        "project_inputs": {
            "capacity_mw": cap_mw,
            "number_of_units": num_units,
            "unit_capacity_mw": round(unit_cap_mw, 2),
            "gross_head_m": gross_head,
            "net_head_m": net_head,
            "design_flow_m3s": design_flow,
            "dam_height_m": dam_height,
            "dam_length_m": dam_length,
            "tunnel_length_km": tunnel_len_km,
            "penstock_length_m": penstock_len_m,
            "state": state,
            "project_type": project_type,
            "turbine_type": turbine_type,
            "dam_type": dam_type,
            "powerhouse_type": powerhouse_type,
            "terrain_type": terrain_type,
        },
        "model_1_materials": materials_predicted,
        "material_intensities_per_mw": material_intensities,
        "model_2_generation": {
            "annual_generation_gwh": pred_gen_gwh,
            "capacity_factor": implied_capacity_factor,
            "capacity_factor_pct": implied_capacity_factor_pct,
        },
        "model_3_cost": cost_predicted,
        "model_4_duration": {
            "construction_duration_months": pred_dur_months,
            "estimated_years": round(pred_dur_months / 12.0, 1),
        },
        "rag_confidence": confidence_data,
        "government_sources": get_government_citations(),
        "summary": f"ConstructIQ 4-Model estimate for {cap_mw} MW Hydro project in {state}: {materials_predicted['concrete_m3']:,} m3 concrete, {pred_gen_gwh:,} annual GWh, Total Cost INR {cost_predicted['total_project_cost_cr']:,} Cr, Duration {pred_dur_months} months ({confidence_data['confidence_score_pct']}% Confidence)."
    }

if __name__ == "__main__":
    sample_req = {"capacity_mw": 250.0, "net_head_m": 180.0, "state": "Uttarakhand", "number_of_units": 4}
    res = run_estimation_pipeline(sample_req)
    print("\n[ORCHESTRATOR PIPELINE SUCCESS]")
    print(json.dumps(res, indent=2))
