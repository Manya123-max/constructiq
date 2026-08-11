# -*- coding: utf-8 -*-
"""
ConstructIQ - 4-Model Anti-Data-Leakage ML Model Training Script.
Trains 4 distinct ML models exclusively for Hydro Power Projects:
1. Model 1 — Material Estimation Model (Random Forest / MultiOutput Regressor)
2. Model 2 — Power Generation Model (HistGradientBoosting / GradientBoosting)
3. Model 3 — Project Cost Model (GradientBoosting / MultiOutput Regressor)
4. Model 4 — Construction Duration Model (HistGradientBoosting / GradientBoosting)

Strictly enforces feature isolation to prevent data leakage.
Exports model artifacts to backend/ml/models/
"""

import os
import sys
import io
import json
import joblib
import warnings
import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestRegressor,
    HistGradientBoostingRegressor
)
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import OrdinalEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
MODEL_DIR = os.path.join(BASE_DIR, "ml", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

CATEGORICAL_COLS = ["project_type", "turbine_type", "dam_type", "powerhouse_type", "terrain_type", "state"]

def preprocess_and_encode(df: pd.DataFrame) -> (pd.DataFrame, dict):
    df_encoded = df.copy()
    encoders = {}
    for col in CATEGORICAL_COLS:
        if col in df_encoded.columns:
            df_encoded[col] = df_encoded[col].fillna("Unknown").astype(str)
            encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
            df_encoded[col] = encoder.fit_transform(df_encoded[[col]])
            encoders[col] = encoder
    return df_encoded, encoders

def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include=[np.number]).columns:
        median_val = df_clean[col].median()
        df_clean[col] = df_clean[col].fillna(median_val if not np.isnan(median_val) else 0.0)
    return df_clean

def train_all_models():
    projects_csv = os.path.join(RAW_DATA_DIR, "hydro_projects.csv")
    materials_csv = os.path.join(RAW_DATA_DIR, "hydro_materials.csv")
    cost_csv = os.path.join(RAW_DATA_DIR, "hydro_cost.csv")

    if not os.path.exists(projects_csv):
        print(f"[ERROR] {projects_csv} not found. Run generate_synthetic_data.py first.")
        sys.exit(1)

    print("\n[INFO] Loading Hydro Raw Datasets...")
    df_proj = pd.read_csv(projects_csv)
    df_mat = pd.read_csv(materials_csv)
    df_cost = pd.read_csv(cost_csv)

    mat_pivot = df_mat.pivot(index='project_id', columns='material', values='quantity').reset_index()
    mat_columns_rename = {
        "Concrete": "concrete_m3",
        "Cement": "cement_mt",
        "Reinforcement Steel": "reinforcement_steel_mt",
        "Structural Steel": "structural_steel_mt",
        "Penstock Steel": "penstock_steel_mt",
        "Aggregate": "aggregate_m3",
        "Sand": "sand_m3",
        "Excavation": "excavation_m3",
    }
    mat_pivot = mat_pivot.rename(columns=mat_columns_rename)

    df_master = pd.merge(df_proj, mat_pivot, on='project_id', how='left')
    df_master = pd.merge(df_master, df_cost[['project_id', 'civil_cost_cr', 'equipment_cost_cr', 'total_project_cost_cr']], on='project_id', how='left')

    df_master, encoders = preprocess_and_encode(df_master)
    df_master = fill_missing(df_master)

    train_df, test_df = train_test_split(df_master, test_size=0.20, random_state=42)
    print(f"[INFO] Dataset split into {len(train_df)} Training projects and {len(test_df)} Test projects.")

    metrics_summary = {}

    # ─── MODEL 1: Material Estimation Model ─────────────────────────────────
    print("\n[MODEL 1] Training Material Estimation Model (Random Forest MultiOutput)...")
    mat_feature_cols = [
        "capacity_mw", "number_of_units", "gross_head_m", "net_head_m", "design_flow_m3s",
        "dam_height_m", "dam_length_m", "penstock_length_m", "penstock_diameter_m",
        "tunnel_length_km", "tunnel_diameter_m", "reservoir_volume_mcm", "catchment_area_km2",
        "elevation_m", "excavation_volume_m3", "terrain_complexity_score",
        "civil_complexity_score", "hydro_complexity_score",
        "project_type", "turbine_type", "dam_type", "powerhouse_type", "terrain_type", "state"
    ]
    mat_target_cols = [
        "concrete_m3", "cement_mt", "reinforcement_steel_mt",
        "structural_steel_mt", "penstock_steel_mt", "aggregate_m3", "sand_m3", "excavation_m3"
    ]

    X_train_mat = train_df[mat_feature_cols]
    y_train_mat = train_df[mat_target_cols]
    X_test_mat = test_df[mat_feature_cols]
    y_test_mat = test_df[mat_target_cols]

    base_rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    model_mat = MultiOutputRegressor(base_rf)
    model_mat.fit(X_train_mat, y_train_mat)

    preds_mat = model_mat.predict(X_test_mat)
    r2_mat = r2_score(y_test_mat, preds_mat)
    mae_mat = mean_absolute_error(y_test_mat, preds_mat)
    print(f"  -> Material Model R²: {r2_mat:.4f} | MAE: {mae_mat:.2f}")

    joblib.dump(model_mat, os.path.join(MODEL_DIR, "hydro_material_model.joblib"))
    metrics_summary["material_model"] = {"r2": float(r2_mat), "mae": float(mae_mat), "features": mat_feature_cols, "targets": mat_target_cols}

    # ─── MODEL 2: Power Generation Model ────────────────────────────────────
    print("\n[MODEL 2] Training Power Generation Model (HistGradientBoosting)...")
    gen_feature_cols = [
        "capacity_mw", "number_of_units", "gross_head_m", "net_head_m", "design_flow_m3s",
        "annual_inflow_mcm", "reservoir_volume_mcm", "catchment_area_km2",
        "turbine_efficiency", "generator_efficiency", "design_efficiency", "availability_factor",
        "project_type", "turbine_type", "state"
    ]
    gen_target_col = "annual_generation_gwh"

    X_train_gen = train_df[gen_feature_cols]
    y_train_gen = train_df[gen_target_col]
    X_test_gen = test_df[gen_feature_cols]
    y_test_gen = test_df[gen_target_col]

    model_gen = HistGradientBoostingRegressor(max_iter=120, max_depth=6, random_state=42)
    model_gen.fit(X_train_gen, y_train_gen)

    preds_gen = model_gen.predict(X_test_gen)
    r2_gen = r2_score(y_test_gen, preds_gen)
    mae_gen = mean_absolute_error(y_test_gen, preds_gen)
    print(f"  -> Generation Model R²: {r2_gen:.4f} | MAE: {mae_gen:.2f} GWh")

    joblib.dump(model_gen, os.path.join(MODEL_DIR, "hydro_generation_model.joblib"))
    metrics_summary["generation_model"] = {"r2": float(r2_gen), "mae": float(mae_gen), "features": gen_feature_cols, "target": gen_target_col}

    # ─── MODEL 3: Project Cost Model ────────────────────────────────────────
    print("\n[MODEL 3] Training Project Cost Model (Gradient Boosting MultiOutput)...")
    cost_feature_cols = [
        "capacity_mw", "number_of_units", "net_head_m", "dam_height_m", "tunnel_length_km",
        "penstock_length_m", "project_type", "turbine_type", "state", "commissioning_year",
        "concrete_m3", "cement_mt", "reinforcement_steel_mt", "structural_steel_mt",
        "penstock_steel_mt", "aggregate_m3", "sand_m3", "excavation_m3"
    ]
    cost_target_cols = ["civil_cost_cr", "equipment_cost_cr", "total_project_cost_cr"]

    X_train_cost = train_df[cost_feature_cols]
    y_train_cost = train_df[cost_target_cols]
    X_test_cost = test_df[cost_feature_cols]
    y_test_cost = test_df[cost_target_cols]

    base_gbr = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    model_cost = MultiOutputRegressor(base_gbr)
    model_cost.fit(X_train_cost, y_train_cost)

    preds_cost = model_cost.predict(X_test_cost)
    r2_cost = r2_score(y_test_cost, preds_cost)
    mae_cost = mean_absolute_error(y_test_cost, preds_cost)
    print(f"  -> Cost Model R²: {r2_cost:.4f} | MAE: ₹{mae_cost:.2f} Cr")

    joblib.dump(model_cost, os.path.join(MODEL_DIR, "hydro_cost_model.joblib"))
    metrics_summary["cost_model"] = {"r2": float(r2_cost), "mae": float(mae_cost), "features": cost_feature_cols, "targets": cost_target_cols}

    # ─── MODEL 4: Construction Duration Model ───────────────────────────────
    print("\n[MODEL 4] Training Construction Duration Model (Gradient Boosting)...")
    dur_feature_cols = [
        "capacity_mw", "number_of_units", "dam_height_m", "dam_length_m", "tunnel_length_km",
        "tunnel_diameter_m", "penstock_length_m", "excavation_volume_m3", "concrete_m3",
        "terrain_complexity_score", "civil_complexity_score", "hydro_complexity_score",
        "project_type", "dam_type", "powerhouse_type", "state"
    ]
    dur_target_col = "construction_duration_months"

    X_train_dur = train_df[dur_feature_cols]
    y_train_dur = train_df[dur_target_col]
    X_test_dur = test_df[dur_feature_cols]
    y_test_dur = test_df[dur_target_col]

    model_dur = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    model_dur.fit(X_train_dur, y_train_dur)

    preds_dur = model_dur.predict(X_test_dur)
    r2_dur = r2_score(y_test_dur, preds_dur)
    mae_dur = mean_absolute_error(y_test_dur, preds_dur)
    print(f"  -> Duration Model R²: {r2_dur:.4f} | MAE: {mae_dur:.2f} Months")

    joblib.dump(model_dur, os.path.join(MODEL_DIR, "hydro_duration_model.joblib"))
    metrics_summary["duration_model"] = {"r2": float(r2_dur), "mae": float(mae_dur), "features": dur_feature_cols, "target": dur_target_col}

    joblib.dump(encoders, os.path.join(MODEL_DIR, "hydro_encoders.joblib"))
    with open(os.path.join(MODEL_DIR, "model_metrics.json"), "w") as f:
        json.dump(metrics_summary, f, indent=2)

    print("\n[SUCCESS] All 4 Hydro ML Models trained and saved to backend/ml/models/:")
    print("  1. hydro_material_model.joblib")
    print("  2. hydro_generation_model.joblib")
    print("  3. hydro_cost_model.joblib")
    print("  4. hydro_duration_model.joblib")

if __name__ == "__main__":
    train_all_models()
