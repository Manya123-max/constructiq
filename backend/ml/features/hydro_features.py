"""
Hydro project feature engineering.
All engineered features are computed here — never used as input
to the model that predicts the same material (leakage prevention).
"""

import math
import pandas as pd
import numpy as np


ETA_HYDRAULIC = 0.85  # combined hydro efficiency for hydraulic power


def compute_hydro_features(row: dict) -> dict:
    """
    Given a dict of raw hydro project fields, compute all engineered features.
    Returns the original dict augmented with derived features.
    """
    r = dict(row)
    cap = r.get("capacity_mw") or 0
    units = max(r.get("number_of_units", 1) or 1, 1)
    head  = r.get("head_m") or 0
    flow  = r.get("design_flow_m3s") or 0
    dam_h = r.get("dam_height_m") or 0
    plen  = r.get("penstock_length_m") or 0

    # Feature 1: Unit capacity
    r["unit_capacity_mw"] = round(cap / units, 3) if cap else None

    # Feature 2: Hydraulic power  (P = ρgQH × η / 1e6 → MW)
    if head > 0 and flow > 0:
        r["hydraulic_power_mw"] = round(1000 * 9.81 * flow * head * ETA_HYDRAULIC / 1e6, 3)
    else:
        r["hydraulic_power_mw"] = None

    # Feature 3: Capacity / head
    r["capacity_per_head"] = round(cap / head, 4) if head > 0 else None

    # Feature 4: Flow intensity
    r["flow_per_mw"] = round(flow / cap, 4) if cap > 0 else None

    # Feature 5: Dam height category
    r["dam_height_category"] = _categorize_dam_height(dam_h)

    # Feature 6: Penstock intensity
    r["penstock_intensity"] = round(plen / cap, 4) if cap > 0 else None

    return r


def _categorize_dam_height(h: float) -> str:
    if not h or h == 0:
        return "Unknown"
    if h < 30:
        return "Low"
    elif h < 70:
        return "Medium"
    elif h < 150:
        return "High"
    else:
        return "VeryHigh"


def build_hydro_feature_vector(project: dict) -> pd.DataFrame:
    """
    Build the ML-ready feature vector for the material/cost prediction models.
    EXCLUDES intensity features (leakage guard).
    """
    feat = compute_hydro_features(project)
    ml_features = {
        "capacity_mw":          feat.get("capacity_mw"),
        "number_of_units":      feat.get("number_of_units"),
        "head_m":               feat.get("head_m"),
        "design_flow_m3s":      feat.get("design_flow_m3s"),
        "dam_height_m":         feat.get("dam_height_m"),
        "penstock_length_m":    feat.get("penstock_length_m"),
        "tunnel_length_m":      feat.get("tunnel_length_m"),
        "catchment_area_km2":   feat.get("catchment_area_km2"),
        # Engineered — safe (not predicted by material model)
        "unit_capacity_mw":     feat.get("unit_capacity_mw"),
        "hydraulic_power_mw":   feat.get("hydraulic_power_mw"),
        "capacity_per_head":    feat.get("capacity_per_head"),
        "flow_per_mw":          feat.get("flow_per_mw"),
        "penstock_intensity":   feat.get("penstock_intensity"),
        # Categorical → will be encoded at training time
        "plant_type":           feat.get("plant_type", "run-of-river"),
        "turbine_type":         feat.get("turbine_type", "Francis"),
        "dam_height_category":  feat.get("dam_height_category", "Medium"),
    }
    return pd.DataFrame([ml_features])


def compute_material_intensities(project: dict, materials: dict) -> dict:
    """
    Compute intensity features for benchmarking / validation only.
    NEVER feed these back into the model predicting the same material.
    """
    cap = project.get("capacity_mw") or 1
    intensities = {}
    for mat, qty in materials.items():
        if qty and cap:
            intensities[f"{mat}_per_mw"] = round(qty / cap, 4)
    return intensities


def validate_hydro_inputs(data: dict) -> list[str]:
    """Validate hydro inputs and return a list of warnings."""
    warnings = []
    cap  = data.get("capacity_mw", 0) or 0
    head = data.get("head_m", 0) or 0
    flow = data.get("design_flow_m3s", 0) or 0

    if cap <= 0:
        warnings.append("capacity_mw must be positive")
    if head <= 0:
        warnings.append("head_m must be positive")
    if flow <= 0:
        warnings.append("design_flow_m3s must be positive")

    # Sanity: hydraulic power should be close to capacity
    if head > 0 and flow > 0 and cap > 0:
        hydro_mw = 1000 * 9.81 * flow * head * ETA_HYDRAULIC / 1e6
        ratio = cap / hydro_mw
        if ratio > 1.2 or ratio < 0.6:
            warnings.append(
                f"capacity_mw ({cap}) is far from hydraulic power estimate "
                f"({hydro_mw:.1f} MW). Check head/flow values."
            )

    if data.get("number_of_units", 1) < 1:
        warnings.append("number_of_units must be ≥ 1")

    return warnings
