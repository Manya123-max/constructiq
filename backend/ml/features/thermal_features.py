"""
Thermal project feature engineering.
"""

import pandas as pd


def compute_thermal_features(row: dict) -> dict:
    r = dict(row)
    cap   = r.get("capacity_mw") or 0
    units = max(r.get("number_of_units", 1) or 1, 1)
    be    = r.get("boiler_efficiency") or 0
    te    = r.get("turbine_efficiency") or 0
    ge    = r.get("generator_efficiency") or 0
    coal  = r.get("coal_consumption_tpd") or 0
    water = r.get("water_requirement_m3day") or 0
    steam = r.get("steam_flow_tph") or 0

    # Unit capacity
    r["unit_capacity_mw"] = round(cap / units, 3) if cap else None

    # Combined efficiency (boiler × turbine × generator)
    if be > 0 and te > 0 and ge > 0:
        r["combined_efficiency"] = round(be * te * ge, 4)
    else:
        r["combined_efficiency"] = None

    # Coal intensity (strongest predictor)
    r["coal_tpd_per_mw"] = round(coal / cap, 4) if cap > 0 else None

    # Water intensity
    r["water_m3_per_mw"] = round(water / cap, 4) if cap > 0 else None

    # Steam intensity
    r["steam_tph_per_mw"] = round(steam / cap, 4) if cap > 0 else None

    return r


def build_thermal_feature_vector(project: dict) -> pd.DataFrame:
    """Build ML-ready feature vector. Excludes material intensity targets."""
    feat = compute_thermal_features(project)
    ml_features = {
        "capacity_mw":          feat.get("capacity_mw"),
        "number_of_units":      feat.get("number_of_units"),
        "coal_hhv_kcal_kg":     feat.get("coal_hhv_kcal_kg"),
        "steam_pressure_bar":   feat.get("steam_pressure_bar"),
        "steam_temperature_c":  feat.get("steam_temperature_c"),
        "plant_load_factor":    feat.get("plant_load_factor"),
        "coal_consumption_tpd": feat.get("coal_consumption_tpd"),
        "water_requirement_m3day": feat.get("water_requirement_m3day"),
        # Engineered
        "unit_capacity_mw":     feat.get("unit_capacity_mw"),
        "combined_efficiency":  feat.get("combined_efficiency"),
        "coal_tpd_per_mw":      feat.get("coal_tpd_per_mw"),
        "water_m3_per_mw":      feat.get("water_m3_per_mw"),
        "steam_tph_per_mw":     feat.get("steam_tph_per_mw"),
        # Categorical
        "fuel_type":            feat.get("fuel_type", "coal"),
        "cooling_type":         feat.get("cooling_type", "wet_tower"),
        "boiler_type":          feat.get("boiler_type", "pulverized"),
    }
    return pd.DataFrame([ml_features])


def validate_thermal_inputs(data: dict) -> list[str]:
    warnings = []
    cap = data.get("capacity_mw", 0) or 0
    if cap <= 0:
        warnings.append("capacity_mw must be positive")
    if data.get("number_of_units", 1) < 1:
        warnings.append("number_of_units must be ≥ 1")
    plf = data.get("plant_load_factor")
    if plf and (plf < 0.3 or plf > 1.0):
        warnings.append("plant_load_factor should be between 0.3 and 1.0")
    return warnings
