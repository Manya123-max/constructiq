# -*- coding: utf-8 -*-
"""
ConstructIQ - Parametric Synthetic Dataset Generator for Hydro Power Projects.
Generates 400 distinct hydro project records across 6 standard categories:
- Large Hydro (>100 MW): 100 projects
- Medium Hydro (25-100 MW): 100 projects
- Small Hydro (2-25 MW): 100 projects
- Mini Hydro (0.1-2 MW): 40 projects
- Micro Hydro (0.005-0.1 MW): 40 projects
- Pico Hydro (<0.005 MW): 20 projects

Generates 7 raw CSV files under data/raw/:
1. hydro_projects.csv
2. hydro_materials.csv
3. hydro_equipment.csv
4. hydro_generation.csv
5. hydro_cost.csv
6. hydro_reference_intensity.csv
7. hydro_data_dictionary.csv
"""

import sys
import io
import os
import random
import math
import pandas as pd
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# ─── Geography & Basins ───────────────────────────────────────────────────────
RIVER_BASINS = {
    "Ganga Basin": ["Uttarakhand", "Uttar Pradesh", "Bihar", "West Bengal"],
    "Indus Basin": ["Himachal Pradesh", "Jammu & Kashmir", "Ladakh", "Punjab"],
    "Brahmaputra Basin": ["Arunachal Pradesh", "Sikkim", "Assam", "Meghalaya"],
    "Godavari Basin": ["Maharashtra", "Telangana", "Andhra Pradesh", "Odisha", "Madhya Pradesh"],
    "Krishna Basin": ["Maharashtra", "Karnataka", "Telangana", "Andhra Pradesh"],
    "Cauvery Basin": ["Karnataka", "Tamil Nadu", "Kerala"],
    "Narmada Basin": ["Madhya Pradesh", "Gujarat"],
    "Tapti Basin": ["Madhya Pradesh", "Maharashtra", "Gujarat"],
    "West Flowing Rivers": ["Kerala", "Karnataka", "Maharashtra", "Goa"],
}

INDIAN_STATES = list(set([state for states in RIVER_BASINS.values() for state in states]))

RIVERS_BY_BASIN = {
    "Ganga Basin": ["Bhagirathi", "Alaknanda", "Mandakini", "Yamuna", "Teesta", "Kosi", "Gandak"],
    "Indus Basin": ["Sutlej", "Beas", "Ravi", "Chenab", "Jhelum", "Indus"],
    "Brahmaputra Basin": ["Subansiri", "Siang", "Kameng", "Lohit", "Dibang", "Kopili"],
    "Godavari Basin": ["Godavari", "Indravati", "Pranahita", "Wainganga"],
    "Krishna Basin": ["Krishna", "Tungabhadra", "Bhima", "Koyna"],
    "Cauvery Basin": ["Cauvery", "Bhavani", "Kabini", "Moyar"],
    "Narmada Basin": ["Narmada", "Tawa"],
    "Tapti Basin": ["Tapti", "Girna"],
    "West Flowing Rivers": ["Periyar", "Sharavathi", "Kalinadi", "Pamba"],
}

DISTRICTS_BY_STATE = {
    "Uttarakhand": ["Uttarkashi", "Chamoli", "Pithoragarh", "Rudraprayag", "Tehri Garhwal"],
    "Himachal Pradesh": ["Kullu", "Mandi", "Chamba", "Kinnaur", "Lahaul & Spiti", "Shimla"],
    "Jammu & Kashmir": ["Kishtwar", "Reasi", "Ganderbal", "Baramulla", "Anantnag"],
    "Ladakh": ["Leh", "Kargil"],
    "Sikkim": ["North Sikkim", "West Sikkim", "South Sikkim"],
    "Arunachal Pradesh": ["Lower Subansiri", "West Kameng", "East Siang", "Tawang"],
    "Assam": ["Dima Hasao", "Karbi Anglong"],
    "Meghalaya": ["West Khasi Hills", "Ri-Bhoi"],
    "Kerala": ["Idukki", "Wayanad", "Pathanamthitta"],
    "Karnataka": ["Shivamogga", "Uttara Kannada", "Chikmagalur"],
    "Maharashtra": ["Satara", "Pune", "Nashik", "Kolhapur"],
    "Andhra Pradesh": ["Kurnool", "Alluri Sitharama Raju"],
    "Telangana": ["Nalgonda", "Bhadradri Kothagudem"],
    "Odisha": ["Koraput", "Rayagada"],
    "Madhya Pradesh": ["Khandwa", "Hoshangabad", "Jabalpur"],
    "Gujarat": ["Narmada"],
    "West Bengal": ["Darjeeling", "Kalimpong"],
    "Uttar Pradesh": ["Sonbhadra"],
    "Bihar": ["Kaimur"],
    "Punjab": ["Pathankot"],
    "Goa": ["North Goa"],
}

HYDRO_PROJECT_NAME_PREFIXES = [
    "Subansiri", "Teesta", "Kishanganga", "Ratle", "Pakal Dul", "Kwar", "Kiru",
    "Sutlej", "Parbati", "Koldam", "Chamera", "Nathpa Jhakri", "Rampur", "Luhri",
    "SVP Sharavathi", "Koyna", "Idukki", "Srisailam", "Nagarjunasagar", "Omkareshwar",
    "Indirasagar", "Sardar Sarovar", "Tehri", "Koteshwar", "Tapovan Vishnugad",
    "Lata Tapovan", "Singoli Bhatwari", "Vishnugad Pipalkoti", "Vyasi", "Shanan",
    "Bassu", "Sanjay", "Ghanvi", "Allain Duhangan", "Sawra Kuddu", "Tidong",
    "Budhil", "Chhatru", "Malana", "Bhabha", "Rongtong", "Kargil", "Chutak", "Nimo Bazgo"
]

def get_hydro_category(cap_mw: float) -> str:
    if cap_mw > 100.0:
        return "Large Hydro"
    elif cap_mw >= 25.0:
        return "Medium Hydro"
    elif cap_mw >= 2.0:
        return "Small Hydro"
    elif cap_mw >= 0.1:
        return "Mini Hydro"
    elif cap_mw >= 0.005:
        return "Micro Hydro"
    else:
        return "Pico Hydro"

# ─── Reference Anchors Table Definition ──────────────────────────────────────
REFERENCE_INTENSITIES = [
    {
        "category": "Large Hydro",
        "concrete_m3_min": 800000, "concrete_m3_max": 1500000,
        "rebar_mt_min": 15000, "rebar_mt_max": 40000,
        "penstock_steel_mt_min": 3000, "penstock_steel_mt_max": 10000,
        "excavation_m3_min": 5000000, "excavation_m3_max": 20000000,
        "scope_description": "Major dam, spillway, headrace tunnel, underground powerhouse, tailrace tunnel"
    },
    {
        "category": "Medium Hydro",
        "concrete_m3_min": 50000, "concrete_m3_max": 200000,
        "rebar_mt_min": 2000, "rebar_mt_max": 8000,
        "penstock_steel_mt_min": 500, "penstock_steel_mt_max": 2000,
        "excavation_m3_min": 500000, "excavation_m3_max": 3000000,
        "scope_description": "Diversion weir/barrage, desilting basin, headrace channel/tunnel, surface/underground powerhouse"
    },
    {
        "category": "Small Hydro",
        "concrete_m3_min": 5000, "concrete_m3_max": 30000,
        "rebar_mt_min": 300, "rebar_mt_max": 1500,
        "penstock_steel_mt_min": 100, "penstock_steel_mt_max": 500,
        "excavation_m3_min": 50000, "excavation_m3_max": 300000,
        "scope_description": "Trench intake/weir, power channel, forebay, penstock, surface powerhouse"
    },
    {
        "category": "Mini Hydro",
        "concrete_m3_min": 500, "concrete_m3_max": 3000,
        "rebar_mt_min": 30, "rebar_mt_max": 150,
        "penstock_steel_mt_min": 10, "penstock_steel_mt_max": 50,
        "excavation_m3_min": 5000, "excavation_m3_max": 30000,
        "scope_description": "Small intake, canal, pipe penstock, compact surface powerhouse"
    },
    {
        "category": "Micro Hydro",
        "concrete_m3_min": 20, "concrete_m3_max": 200,
        "rebar_mt_min": 2, "rebar_mt_max": 15,
        "penstock_steel_mt_min": 1, "penstock_steel_mt_max": 5,
        "excavation_m3_min": 500, "excavation_m3_max": 3000,
        "scope_description": "Run-of-river intake, HDPE/steel pipe, small civil base, shed"
    },
    {
        "category": "Pico Hydro",
        "concrete_m3_min": 1, "concrete_m3_max": 10,
        "rebar_mt_min": 0.1, "rebar_mt_max": 1,
        "penstock_steel_mt_min": 0.05, "penstock_steel_mt_max": 0.5,
        "excavation_m3_min": 20, "excavation_m3_max": 200,
        "scope_description": "Ultra-compact intake pipe, micro-turbine frame, minimal masonry"
    }
]

# ─── Data Generation Routine ──────────────────────────────────────────────────
def generate_all_datasets():
    # 400 Projects Distribution
    categories_config = [
        ("Large Hydro", 100, (100.1, 2000.0)),
        ("Medium Hydro", 100, (25.0, 100.0)),
        ("Small Hydro", 100, (2.0, 24.9)),
        ("Mini Hydro", 40, (0.1, 1.99)),
        ("Micro Hydro", 40, (0.005, 0.099)),
        ("Pico Hydro", 20, (0.0005, 0.0049)),
    ]

    projects_list = []
    materials_list = []
    equipment_list = []
    generation_list = []
    cost_list = []

    project_counter = 1

    for cat_name, count, (min_cap, max_cap) in categories_config:
        for i in range(count):
            proj_id = f"HP-{project_counter:03d}"
            
            # Select State & Basin
            state = random.choice(INDIAN_STATES)
            basin = None
            for b_name, s_list in RIVER_BASINS.items():
                if state in s_list:
                    basin = b_name
                    break
            if not basin:
                basin = "Ganga Basin"
            
            river = random.choice(RIVERS_BY_BASIN.get(basin, ["Mountain River"]))
            dist_list = DISTRICTS_BY_STATE.get(state, ["Central District"])
            district = random.choice(dist_list)
            
            name_prefix = random.choice(HYDRO_PROJECT_NAME_PREFIXES)
            proj_name = f"{name_prefix} Hydro Project Unit-{project_counter}"
            
            # Capacity MW
            if cat_name == "Large Hydro":
                # Uniform/log normal spread
                cap_mw = round(random.uniform(min_cap, max_cap), 2)
            elif cat_name == "Medium Hydro":
                cap_mw = round(random.uniform(min_cap, max_cap), 2)
            elif cat_name == "Small Hydro":
                cap_mw = round(random.uniform(min_cap, max_cap), 2)
            elif cat_name == "Mini Hydro":
                cap_mw = round(random.uniform(min_cap, max_cap), 3)
            elif cat_name == "Micro Hydro":
                cap_mw = round(random.uniform(min_cap, max_cap), 4)
            else:
                cap_mw = round(random.uniform(min_cap, max_cap), 5)
            
            # Plant & Terrain parameters
            if cap_mw >= 100:
                plant_type = random.choice(["storage", "run-of-river", "pumped"])
                terrain_type = random.choice(["Mountainous", "Gorge", "Hilly"])
                dev_type = random.choice(["Greenfield", "Greenfield", "Brownfield"])
            elif cap_mw >= 2:
                plant_type = random.choice(["run-of-river", "run-of-river", "storage"])
                terrain_type = random.choice(["Hilly", "Mountainous", "Plain"])
                dev_type = random.choice(["Greenfield", "Refurbishment"])
            else:
                plant_type = "run-of-river"
                terrain_type = random.choice(["Hilly", "Mountainous", "Plain"])
                dev_type = "Greenfield"
                
            elevation_m = round(random.uniform(100.0, 3200.0), 1)
            climate_zone = "Alpine" if elevation_m > 2200 else ("Himalayan Sub-tropical" if elevation_m > 800 else "Tropical")
            
            # Units configuration
            if cap_mw > 500:
                num_units = random.choice([4, 6, 8])
            elif cap_mw > 100:
                num_units = random.choice([3, 4, 5, 6])
            elif cap_mw > 25:
                num_units = random.choice([2, 3, 4])
            elif cap_mw > 2:
                num_units = random.choice([2, 3])
            elif cap_mw > 0.05:
                num_units = random.choice([1, 2])
            else:
                num_units = 1
                
            unit_cap_mw = round(cap_mw / num_units, 4)
            comm_year = random.randint(2000, 2022)
            proj_life = random.choice([35, 40, 50])
            
            # Gross Head & Net Head
            if cat_name in ["Large Hydro", "Medium Hydro"]:
                gross_head_m = round(random.uniform(40.0, 550.0), 1)
            elif cat_name in ["Small Hydro", "Mini Hydro"]:
                gross_head_m = round(random.uniform(15.0, 250.0), 1)
            else:
                gross_head_m = round(random.uniform(5.0, 80.0), 1)
                
            head_loss_pct = random.uniform(0.03, 0.08)
            net_head_m = round(gross_head_m * (1.0 - head_loss_pct), 1)
            
            # Design Flow (Q) using Hydraulic Power Formula P = rho * g * Q * H * eta
            # eta approx 0.90
            target_power_w = cap_mw * 1e6
            rho_g = 9810.0
            eta_sys = random.uniform(0.88, 0.94)
            design_flow_m3s = round(target_power_w / (rho_g * net_head_m * eta_sys), 3)
            
            # Hydraulic noise variation (~3.12%)
            noise_factor = random.uniform(0.965, 1.035)
            design_flow_m3s = round(design_flow_m3s * noise_factor, 3)
            
            min_flow_m3s = round(design_flow_m3s * random.uniform(0.1, 0.2), 3)
            max_flow_m3s = round(design_flow_m3s * random.uniform(1.2, 1.5), 3)
            annual_inflow_mcm = round(design_flow_m3s * 31.536 * random.uniform(0.5, 1.1), 2)
            
            if cap_mw >= 100:
                catchment_area_km2 = round(random.uniform(500.0, 15000.0), 1)
                reservoir_vol_mcm = round(random.uniform(20.0, 2500.0), 1) if plant_type == "storage" else round(random.uniform(0.5, 15.0), 1)
            elif cap_mw >= 2:
                catchment_area_km2 = round(random.uniform(50.0, 1200.0), 1)
                reservoir_vol_mcm = round(random.uniform(2.0, 50.0), 1) if plant_type == "storage" else round(random.uniform(0.1, 2.0), 1)
            else:
                catchment_area_km2 = round(random.uniform(2.0, 50.0), 1)
                reservoir_vol_mcm = round(random.uniform(0.01, 0.5), 3)
                
            # Civil Structures
            if plant_type == "storage":
                dam_type = random.choice(["Concrete Gravity", "RCC", "Rockfill", "Earthfill"])
                dam_height_m = round(random.uniform(40.0, 230.0), 1) if cap_mw > 25 else round(random.uniform(15.0, 60.0), 1)
                dam_length_m = round(dam_height_m * random.uniform(2.5, 6.0), 1)
                res_area_km2 = round(reservoir_vol_mcm * random.uniform(0.05, 0.2), 2)
            else: # run-of-river
                dam_type = random.choice(["Barrage/Weir", "Trench Intake", "Concrete Gravity"])
                dam_height_m = round(random.uniform(5.0, 35.0), 1) if cap_mw > 25 else round(random.uniform(2.0, 15.0), 1)
                dam_length_m = round(dam_height_m * random.uniform(3.0, 8.0), 1)
                res_area_km2 = round(reservoir_vol_mcm * 0.1, 2)
                
            if cat_name in ["Large Hydro", "Medium Hydro"]:
                tunnel_length_km = round(random.uniform(2.0, 22.0), 2)
                tunnel_diameter_m = round(random.uniform(4.0, 11.0), 2)
                penstock_length_m = round(random.uniform(150.0, 1200.0), 1)
                penstock_diameter_m = round(random.uniform(2.5, 7.5), 2)
                powerhouse_type = random.choice(["Underground", "Surface", "Semi-underground"])
                powerhouse_area_m2 = round(cap_mw * random.uniform(8.0, 18.0), 1)
            elif cat_name == "Small Hydro":
                tunnel_length_km = round(random.uniform(0.0, 4.0), 2)
                tunnel_diameter_m = round(random.uniform(2.0, 4.5), 2) if tunnel_length_km > 0 else 0.0
                penstock_length_m = round(random.uniform(80.0, 500.0), 1)
                penstock_diameter_m = round(random.uniform(1.2, 3.0), 2)
                powerhouse_type = "Surface"
                powerhouse_area_m2 = round(cap_mw * random.uniform(15.0, 30.0), 1)
            else: # Mini, Micro, Pico
                tunnel_length_km = 0.0
                tunnel_diameter_m = 0.0
                penstock_length_m = round(random.uniform(10.0, 120.0), 1)
                penstock_diameter_m = round(random.uniform(0.2, 1.0), 2)
                powerhouse_type = "Surface"
                powerhouse_area_m2 = round(max(10.0, cap_mw * 100.0), 1)
                
            # Turbine Type based on Head & Flow
            if net_head_m > 250.0:
                turbine_type = "Pelton"
            elif net_head_m > 45.0:
                turbine_type = "Francis"
            elif net_head_m > 10.0:
                turbine_type = "Kaplan" if design_flow_m3s > 5.0 else "Francis"
            else:
                turbine_type = "Kaplan" if cap_mw > 0.1 else "Cross-flow"
                
            turbine_eff = round(random.uniform(0.91, 0.95), 3)
            gen_eff = round(random.uniform(0.95, 0.98), 3)
            sys_eff = round(turbine_eff * gen_eff, 3)
            
            # Complexity Scores
            terrain_comp = round(random.uniform(1.5, 4.8), 1)
            civil_comp = round(random.uniform(1.2, 4.9), 1)
            hydro_comp = round(random.uniform(1.3, 4.7), 1)
            overall_comp = round((terrain_comp + civil_comp + hydro_comp) / 3.0, 1)
            
            # Materials Estimation Logic based on physics & category anchors
            var = random.uniform(0.92, 1.08) # 5-10% stochastic interacting variation
            ref = next(r for r in REFERENCE_INTENSITIES if r["category"] == cat_name)
            
            if cat_name == "Large Hydro":
                ratio = min(1.0, max(0.0, (cap_mw - 100.0) / 1900.0))
                concrete_m3 = (800000 + ratio * 700000) * var + (dam_height_m * 1200) + (tunnel_length_km * 25000)
                rebar_mt = (15000 + ratio * 25000) * var
                penstock_steel_mt = (3000 + ratio * 7000) * var + (penstock_length_m * penstock_diameter_m * 1.5)
                excavation_m3 = (5000000 + ratio * 15000000) * var + (tunnel_length_km * 180000)
            elif cat_name == "Medium Hydro":
                ratio = (cap_mw - 25.0) / 75.0
                concrete_m3 = (50000 + ratio * 150000) * var + (dam_height_m * 600) + (tunnel_length_km * 10000)
                rebar_mt = (2000 + ratio * 6000) * var
                penstock_steel_mt = (500 + ratio * 1500) * var + (penstock_length_m * penstock_diameter_m * 1.2)
                excavation_m3 = (500000 + ratio * 2500000) * var
            elif cat_name == "Small Hydro":
                ratio = (cap_mw - 2.0) / 23.0
                concrete_m3 = (5000 + ratio * 25000) * var
                rebar_mt = (300 + ratio * 1200) * var
                penstock_steel_mt = (100 + ratio * 400) * var
                excavation_m3 = (50000 + ratio * 250000) * var
            elif cat_name == "Mini Hydro":
                ratio = (cap_mw - 0.1) / 1.9
                concrete_m3 = (500 + ratio * 2500) * var
                rebar_mt = (30 + ratio * 120) * var
                penstock_steel_mt = (10 + ratio * 40) * var
                excavation_m3 = (5000 + ratio * 25000) * var
            elif cat_name == "Micro Hydro":
                ratio = (cap_mw - 0.005) / 0.095
                concrete_m3 = (20 + ratio * 180) * var
                rebar_mt = (2 + ratio * 13) * var
                penstock_steel_mt = (1 + ratio * 4) * var
                excavation_m3 = (500 + ratio * 2500) * var
            else: # Pico
                concrete_m3 = random.uniform(1.0, 9.5) * var
                rebar_mt = random.uniform(0.05, 0.95) * var
                penstock_steel_mt = random.uniform(0.02, 0.45) * var
                excavation_m3 = random.uniform(15.0, 180.0) * var

            concrete_m3 = round(concrete_m3, 1)
            rebar_mt = round(rebar_mt, 1)
            penstock_steel_mt = round(penstock_steel_mt, 1)
            excavation_m3 = round(excavation_m3, 1)
            
            # Derived sub-materials
            cement_mt = round(concrete_m3 * 0.35, 1) # ~350kg cement per m3 concrete
            aggregate_m3 = round(concrete_m3 * 0.85, 1)
            sand_m3 = round(concrete_m3 * 0.45, 1)
            struct_steel_mt = round(rebar_mt * random.uniform(0.20, 0.35), 1)
            rock_excavation_m3 = round(excavation_m3 * (0.75 if terrain_type == "Mountainous" else 0.45), 1)
            earth_excavation_m3 = round(excavation_m3 - rock_excavation_m3, 1)
            grouting_cement_mt = round(cement_mt * 0.08, 1)
            shotcrete_m3 = round(concrete_m3 * (0.12 if tunnel_length_km > 0 else 0.02), 1)
            lining_concrete_m3 = round(concrete_m3 * (0.25 if tunnel_length_km > 0 else 0.05), 1)
            gates_steel_mt = round(rebar_mt * 0.05, 1)
            embedded_steel_mt = round(struct_steel_mt * 0.15, 1)
            
            # Per MW Intensity Metrics (FOR VALIDATION / DERIVED ONLY - LEAKAGE IF USED IN ML)
            concrete_per_mw = round(concrete_m3 / cap_mw, 2)
            cement_per_mw = round(cement_mt / cap_mw, 2)
            rebar_per_mw = round(rebar_mt / cap_mw, 2)
            struct_steel_per_mw = round(struct_steel_mt / cap_mw, 2)
            penstock_steel_per_mw = round(penstock_steel_mt / cap_mw, 2)
            excavation_per_mw = round(excavation_m3 / cap_mw, 2)

            # Generation Outcomes
            # Target Capacity Factor: 40% - 65% for storage/ROR
            cap_factor = round(random.uniform(0.38, 0.62), 3)
            avail_factor = round(random.uniform(0.86, 0.95), 3)
            ann_operating_hours = round(avail_factor * 8760.0, 1)
            annual_gen_gwh = round(cap_mw * cap_factor * 8760.0 / 1000.0, 2)
            # Add ~1.22% generation variation noise
            annual_gen_gwh = round(annual_gen_gwh * random.uniform(0.988, 1.012), 2)
            plf_pct = round(cap_factor * 100.0, 2)

            # Construction Duration (Months)
            if cat_name == "Large Hydro":
                base_duration = random.uniform(60, 90) + (dam_height_m * 0.10) + (tunnel_length_km * 0.8)
                base_duration = min(120.0, base_duration)
            elif cat_name == "Medium Hydro":
                base_duration = random.uniform(36, 60) + (dam_height_m * 0.08)
                base_duration = min(72.0, base_duration)
            elif cat_name == "Small Hydro":
                base_duration = random.uniform(24, 36)
            elif cat_name == "Mini Hydro":
                base_duration = random.uniform(14, 24)
            elif cat_name == "Micro Hydro":
                base_duration = random.uniform(8, 14)
            else:
                base_duration = random.uniform(3, 8)
                
            total_duration_months = round(base_duration, 1)
            civil_dur = round(total_duration_months * random.uniform(0.55, 0.65), 1)
            dam_dur = round(total_duration_months * random.uniform(0.35, 0.45), 1)
            tunnel_dur = round(total_duration_months * random.uniform(0.30, 0.45), 1) if tunnel_length_km > 0 else 0.0
            powerhouse_dur = round(total_duration_months * random.uniform(0.25, 0.35), 1)
            em_install_dur = round(total_duration_months * random.uniform(0.20, 0.30), 1)

            # Costs (₹ Crore)
            # Benchmark cost per MW: Large 9-14 Cr/MW, Medium 8-12 Cr/MW, Small 7-10 Cr/MW, Mini 6-9 Cr/MW
            if cap_mw >= 100:
                cost_per_mw = random.uniform(9.0, 14.0)
            elif cap_mw >= 25:
                cost_per_mw = random.uniform(8.0, 12.0)
            elif cap_mw >= 2:
                cost_per_mw = random.uniform(7.0, 10.0)
            elif cap_mw >= 0.1:
                cost_per_mw = random.uniform(6.0, 9.0)
            elif cap_mw >= 0.005:
                cost_per_mw = random.uniform(5.0, 8.0)
            else:
                cost_per_mw = random.uniform(4.0, 7.0)
                
            total_cost_cr = round(max(0.1, cap_mw * cost_per_mw * random.uniform(0.93, 1.07)), 2)
            civil_cost_cr = round(total_cost_cr * random.uniform(0.48, 0.58), 2)
            equipment_cost_cr = round(total_cost_cr * random.uniform(0.25, 0.35), 2)
            material_cost_cr = round(civil_cost_cr * random.uniform(0.40, 0.50), 2)
            em_cost_cr = round(equipment_cost_cr * 0.70, 2)
            hm_cost_cr = round(equipment_cost_cr * 0.30, 2)
            infra_cost_cr = round(total_cost_cr * 0.05, 2)
            land_rehab_cost_cr = round(total_cost_cr * 0.04, 2)
            contingency_cost_cr = round(total_cost_cr * 0.03, 2)
            
            # Controlled missingness in optional engineering fields
            crane_cap = round(random.uniform(10.0, 300.0), 1) if (cap_mw > 2.0 and random.random() > 0.15) else None
            res_area_opt = res_area_km2 if random.random() > 0.10 else None

            # Project Row
            proj_dict = {
                "project_id": proj_id,
                "project_name": proj_name,
                "project_category": cat_name,
                "project_type": plant_type,
                "state": state,
                "district": district,
                "river": river,
                "river_basin": basin,
                "terrain_type": terrain_type,
                "development_type": dev_type,
                "climate_zone": climate_zone,
                "elevation_m": elevation_m,
                "capacity_mw": cap_mw,
                "number_of_units": num_units,
                "unit_capacity_mw": unit_cap_mw,
                "commissioning_year": comm_year,
                "project_life_years": proj_life,
                "gross_head_m": gross_head_m,
                "net_head_m": net_head_m,
                "design_flow_m3s": design_flow_m3s,
                "minimum_flow_m3s": min_flow_m3s,
                "maximum_flow_m3s": max_flow_m3s,
                "annual_inflow_mcm": annual_inflow_mcm,
                "catchment_area_km2": catchment_area_km2,
                "reservoir_volume_mcm": reservoir_vol_mcm,
                "dam_type": dam_type,
                "dam_height_m": dam_height_m,
                "dam_length_m": dam_length_m,
                "reservoir_area_km2": res_area_opt,
                "tunnel_length_km": tunnel_length_km,
                "tunnel_diameter_m": tunnel_diameter_m,
                "penstock_length_m": penstock_length_m,
                "penstock_diameter_m": penstock_diameter_m,
                "powerhouse_type": powerhouse_type,
                "powerhouse_area_m2": powerhouse_area_m2,
                "excavation_volume_m3": excavation_m3,
                "turbine_type": turbine_type,
                "turbine_efficiency": turbine_eff,
                "generator_efficiency": gen_eff,
                "design_efficiency": sys_eff,
                "number_of_turbines": num_units,
                "number_of_generators": num_units,
                "transformer_count": num_units + (1 if cap_mw > 100 else 0),
                "transformer_capacity_mva": round((unit_cap_mw / 0.85) * 1.1, 2),
                "crane_capacity_t": crane_cap,
                "penstock_sections": min(4, num_units),
                "project_complexity_score": overall_comp,
                "terrain_complexity_score": terrain_comp,
                "civil_complexity_score": civil_comp,
                "hydro_complexity_score": hydro_comp,
                "annual_generation_gwh": annual_gen_gwh,
                "capacity_factor": cap_factor,
                "plant_load_factor": plf_pct,
                "availability_factor": avail_factor,
                "annual_operating_hours": ann_operating_hours,
                "construction_duration_months": total_duration_months,
                "civil_construction_months": civil_dur,
                "dam_construction_months": dam_dur,
                "tunnel_construction_months": tunnel_dur,
                "powerhouse_construction_months": powerhouse_dur,
                "electromechanical_installation_months": em_install_dur,
                "concrete_m3_per_mw": concrete_per_mw,
                "cement_mt_per_mw": cement_per_mw,
                "reinforcement_steel_mt_per_mw": rebar_per_mw,
                "structural_steel_mt_per_mw": struct_steel_per_mw,
                "penstock_steel_mt_per_mw": penstock_steel_per_mw,
                "excavation_m3_per_mw": excavation_per_mw,
                "synthetic_generation_version": "v1.0",
                "generation_seed": SEED,
                "source_type": "synthetic",
            }
            projects_list.append(proj_dict)

            # Materials Table Rows
            mat_rows = [
                ("Concrete", concrete_m3, "m3", "Civil", concrete_per_mw),
                ("Cement", cement_mt, "MT", "Civil", cement_per_mw),
                ("Reinforcement Steel", rebar_mt, "MT", "Civil", rebar_per_mw),
                ("Structural Steel", struct_steel_mt, "MT", "Civil", struct_steel_per_mw),
                ("Penstock Steel", penstock_steel_mt, "MT", "Hydromechanical", penstock_steel_per_mw),
                ("Aggregate", aggregate_m3, "m3", "Civil", round(aggregate_m3 / cap_mw, 2)),
                ("Sand", sand_m3, "m3", "Civil", round(sand_m3 / cap_mw, 2)),
                ("Excavation", excavation_m3, "m3", "Civil", excavation_per_mw),
                ("Rock Excavation", rock_excavation_m3, "m3", "Civil", round(rock_excavation_m3 / cap_mw, 2)),
                ("Earth Excavation", earth_excavation_m3, "m3", "Civil", round(earth_excavation_m3 / cap_mw, 2)),
                ("Grouting Cement", grouting_cement_mt, "MT", "Civil", round(grouting_cement_mt / cap_mw, 2)),
                ("Shotcrete", shotcrete_m3, "m3", "Civil", round(shotcrete_m3 / cap_mw, 2)),
                ("Lining Concrete", lining_concrete_m3, "m3", "Civil", round(lining_concrete_m3 / cap_mw, 2)),
                ("Gates Steel", gates_steel_mt, "MT", "Hydromechanical", round(gates_steel_mt / cap_mw, 2)),
                ("Embedded Steel", embedded_steel_mt, "MT", "Civil", round(embedded_steel_mt / cap_mw, 2)),
            ]
            for m_name, qty, unit, cat_work, qty_mw in mat_rows:
                materials_list.append({
                    "project_id": proj_id,
                    "material": m_name,
                    "quantity": qty,
                    "unit": unit,
                    "work_category": cat_work,
                    "quantity_per_mw": qty_mw,
                    "data_type": "synthetic",
                    "synthetic_flag": True,
                })

            # Equipment Table Rows
            equipment_list.append({
                "project_id": proj_id, "equipment_type": "Turbine", "quantity": num_units,
                "capacity_per_unit": unit_cap_mw, "unit_of_measure": "MW", "technology": turbine_type
            })
            equipment_list.append({
                "project_id": proj_id, "equipment_type": "Generator", "quantity": num_units,
                "capacity_per_unit": unit_cap_mw, "unit_of_measure": "MW", "technology": "Synchronous Hydro Generator"
            })
            equipment_list.append({
                "project_id": proj_id, "equipment_type": "Main Transformer", "quantity": num_units + (1 if cap_mw > 100 else 0),
                "capacity_per_unit": round((unit_cap_mw / 0.85) * 1.1, 2), "unit_of_measure": "MVA", "technology": "Step-up Power Transformer"
            })
            if crane_cap:
                equipment_list.append({
                    "project_id": proj_id, "equipment_type": "EOT Crane", "quantity": 1 if cap_mw < 100 else 2,
                    "capacity_per_unit": crane_cap, "unit_of_measure": "Tonne", "technology": "Overhead EOT Crane"
                })

            # Generation History Row
            generation_list.append({
                "project_id": proj_id,
                "year": comm_year + 1,
                "generation_gwh": annual_gen_gwh,
                "capacity_factor": cap_factor,
                "availability_factor": avail_factor,
                "annual_inflow_mcm": annual_inflow_mcm,
                "synthetic_flag": True,
            })

            # Cost Row
            cost_list.append({
                "project_id": proj_id,
                "civil_cost_cr": civil_cost_cr,
                "equipment_cost_cr": equipment_cost_cr,
                "material_cost_cr": material_cost_cr,
                "electromechanical_cost_cr": em_cost_cr,
                "hydromechanical_cost_cr": hm_cost_cr,
                "infrastructure_cost_cr": infra_cost_cr,
                "land_rehabilitation_cost_cr": land_rehab_cost_cr,
                "contingency_cost_cr": contingency_cost_cr,
                "total_project_cost_cr": total_cost_cr,
                "cost_year": comm_year,
                "base_year": 2022,
                "normalized_cost_cr": round(total_cost_cr * (1.05 ** (2022 - comm_year)), 2),
                "synthetic_flag": True,
            })

            project_counter += 1

    # Convert to DataFrames
    df_projects = pd.DataFrame(projects_list)
    df_materials = pd.DataFrame(materials_list)
    df_equipment = pd.DataFrame(equipment_list)
    df_generation = pd.DataFrame(generation_list)
    df_cost = pd.DataFrame(cost_list)
    df_ref = pd.DataFrame(REFERENCE_INTENSITIES)

    # Data Dictionary Table
    dict_rows = []
    for col in df_projects.columns:
        dict_rows.append({
            "column_name": col, "table_name": "hydro_projects",
            "description": f"Project feature {col}", "unit": "various",
            "data_type": str(df_projects[col].dtype), "source_type": "synthetic",
            "input_or_target": "target" if "cost" in col or "generation" in col or "duration" in col else "input",
            "derived_flag": col.endswith("_per_mw") or col.endswith("_score"),
            "allowed_range": f"min: {df_projects[col].min()} max: {df_projects[col].max()}",
            "generation_logic": "Constraint-based synthetic hydro physics formula"
        })
    df_dictionary = pd.DataFrame(dict_rows)

    # Save to CSV files in data/raw
    df_projects.to_csv(os.path.join(RAW_DATA_DIR, "hydro_projects.csv"), index=False)
    df_materials.to_csv(os.path.join(RAW_DATA_DIR, "hydro_materials.csv"), index=False)
    df_equipment.to_csv(os.path.join(RAW_DATA_DIR, "hydro_equipment.csv"), index=False)
    df_generation.to_csv(os.path.join(RAW_DATA_DIR, "hydro_generation.csv"), index=False)
    df_cost.to_csv(os.path.join(RAW_DATA_DIR, "hydro_cost.csv"), index=False)
    df_ref.to_csv(os.path.join(RAW_DATA_DIR, "hydro_reference_intensity.csv"), index=False)
    df_dictionary.to_csv(os.path.join(RAW_DATA_DIR, "hydro_data_dictionary.csv"), index=False)

    print(f"[SUCCESS] Generated 400 Hydro projects synthetic dataset into {RAW_DATA_DIR}:")
    print(f"  - hydro_projects.csv ({len(df_projects)} rows)")
    print(f"  - hydro_materials.csv ({len(df_materials)} rows)")
    print(f"  - hydro_equipment.csv ({len(df_equipment)} rows)")
    print(f"  - hydro_generation.csv ({len(df_generation)} rows)")
    print(f"  - hydro_cost.csv ({len(df_cost)} rows)")
    print(f"  - hydro_reference_intensity.csv ({len(df_ref)} rows)")
    print(f"  - hydro_data_dictionary.csv ({len(df_dictionary)} rows)")

if __name__ == "__main__":
    generate_all_datasets()
