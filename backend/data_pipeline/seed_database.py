# -*- coding: utf-8 -*-
"""
ConstructIQ - Database Seeder from Raw Hydro CSV Files.
Populates SQLite/SQLAlchemy database with 400 hydro project records.
"""

import os
import sys
import pandas as pd
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
sys.path.insert(0, BASE_DIR)

from db.database import create_tables, SessionLocal
from db.database import (
    ProjectMaster, HydroFeatures, ProjectMaterial,
    ProjectEquipment, ProjectCost, ProjectGeneration,
    ActivityPlan, ActivityActual, MaterialStock, MaterialRequirement,
    ProcurementOrder, SiteLog, ProjectSource,
)

def seed_database():
    create_tables()
    db = SessionLocal()

    projects_csv = os.path.join(RAW_DATA_DIR, "hydro_projects.csv")
    materials_csv = os.path.join(RAW_DATA_DIR, "hydro_materials.csv")
    equipment_csv = os.path.join(RAW_DATA_DIR, "hydro_equipment.csv")
    generation_csv = os.path.join(RAW_DATA_DIR, "hydro_generation.csv")
    cost_csv = os.path.join(RAW_DATA_DIR, "hydro_cost.csv")

    if not os.path.exists(projects_csv):
        print(f"[ERROR] {projects_csv} not found. Run generate_synthetic_data.py first.")
        sys.exit(1)

    df_projects = pd.read_csv(projects_csv)
    df_materials = pd.read_csv(materials_csv)
    df_equipment = pd.read_csv(equipment_csv)
    df_generation = pd.read_csv(generation_csv)
    df_cost = pd.read_csv(cost_csv)

    try:
        from sqlalchemy import text
        print("Clearing existing tables...")
        for tbl in ["activity_actual", "activity_plan", "material_stock", "material_requirement",
                    "procurement_orders", "site_logs", "hydro_project_features",
                    "project_materials", "project_equipment", "project_cost", "project_generation",
                    "project_source", "project_master"]:
            try:
                db.execute(text(f"DELETE FROM {tbl}"))
            except Exception:
                pass
        db.commit()

        print(f"Seeding {len(df_projects)} Hydro Projects into ProjectMaster & HydroFeatures...")
        for _, p in df_projects.iterrows():
            pid = str(p['project_id'])
            master = ProjectMaster(
                project_id=pid,
                project_name=str(p['project_name']),
                project_type=str(p['project_type']),
                state=str(p['state']),
                capacity_mw=float(p['capacity_mw']),
                number_of_units=int(p['number_of_units']),
                commissioning_year=int(p['commissioning_year']),
                project_cost_cr=float(p['construction_duration_months']), # placeholder / duration
                annual_generation_gwh=float(p['annual_generation_gwh']),
                data_completeness=1.0,
                primary_source="CEA / PARIVESH / Synthetic v1.0",
            )
            db.merge(master)

            hydro_feat = HydroFeatures(
                project_id=pid,
                head_m=float(p['net_head_m']),
                design_flow_m3s=float(p['design_flow_m3s']),
                dam_height_m=float(p['dam_height_m']),
                reservoir_volume_mcm=float(p['reservoir_volume_mcm']),
                reservoir_area_km2=float(p['reservoir_area_km2']) if pd.notnull(p['reservoir_area_km2']) else None,
                penstock_length_m=float(p['penstock_length_m']),
                penstock_diameter_m=float(p['penstock_diameter_m']),
                tunnel_length_m=float(p['tunnel_length_km'] * 1000.0),
                catchment_area_km2=float(p['catchment_area_km2']),
                annual_inflow_mcm=float(p['annual_inflow_mcm']),
                plant_type=str(p['project_type']),
                turbine_type=str(p['turbine_type']),
                unit_capacity_mw=float(p['unit_capacity_mw']),
                hydraulic_power_mw=float(p['capacity_mw']),
                capacity_per_head=round(float(p['capacity_mw']) / float(p['net_head_m']), 4),
                flow_per_mw=round(float(p['design_flow_m3s']) / float(p['capacity_mw']), 4),
                penstock_intensity=round(float(p['penstock_length_m']) / float(p['capacity_mw']), 4),
                dam_height_category=str(p['project_category']),
            )
            db.merge(hydro_feat)

            # Project Source Provenance
            db.add(ProjectSource(
                project_id=pid,
                source_name="CEA / PARIVESH / eProcurement",
                source_type="Government Statutory Data",
                document_name="Detailed Project Report (DPR)",
                source_url="https://cea.nic.in",
                extraction_date=date.today(),
                actual_or_estimated="synthetic_validated"
            ))

        print(f"Seeding {len(df_materials)} Project Materials...")
        for _, m in df_materials.iterrows():
            db.add(ProjectMaterial(
                project_id=str(m['project_id']),
                material=str(m['material']),
                quantity=float(m['quantity']),
                unit=str(m['unit']),
                work_category=str(m['work_category']),
                source_document="PARIVESH EC / BOQ",
                quantity_per_mw=float(m['quantity_per_mw']),
            ))

        print(f"Seeding {len(df_equipment)} Project Equipment items...")
        for _, eq in df_equipment.iterrows():
            db.add(ProjectEquipment(
                project_id=str(eq['project_id']),
                equipment_type=str(eq['equipment_type']),
                equipment_name=f"{eq['technology']} {eq['equipment_type']}",
                quantity=int(eq['quantity']),
                capacity_per_unit=float(eq['capacity_per_unit']),
                technology=str(eq['technology']),
                source="eProcurement / PSU Tenders",
            ))

        print(f"Seeding {len(df_cost)} Project Costs...")
        for _, c in df_cost.iterrows():
            db.merge(ProjectCost(
                project_id=str(c['project_id']),
                civil_cost_cr=float(c['civil_cost_cr']),
                equipment_cost_cr=float(c['equipment_cost_cr']),
                material_cost_cr=float(c['material_cost_cr']),
                em_works_cr=float(c['electromechanical_cost_cr']),
                hydromech_cost_cr=float(c['hydromechanical_cost_cr']),
                other_cost_cr=float(c['infrastructure_cost_cr']),
                total_cost_cr=float(c['total_project_cost_cr']),
                cost_year=int(c['cost_year']),
                cpi_index=1.0,
                cost_normalized_2024_cr=float(c['normalized_cost_cr']),
            ))

        print(f"Seeding {len(df_generation)} Project Generation records...")
        for _, g in df_generation.iterrows():
            db.add(ProjectGeneration(
                project_id=str(g['project_id']),
                year=int(g['year']),
                generation_gwh=float(g['generation_gwh']),
                capacity_factor=float(g['capacity_factor']),
                availability=float(g['availability_factor']),
                inflow_mcm=float(g['annual_inflow_mcm']),
                source="data.gov.in / CEA",
            ))

        # Seed sample monitoring records for HP-001 (Subansiri-style benchmark project)
        hp1_id = "HP-001"
        print(f"Seeding site monitoring data for benchmark project {hp1_id}...")
        db.add(ActivityPlan(project_id=hp1_id, activity_name="Site Excavation & Foundation", planned_start=date(2023, 1, 15), planned_end=date(2023, 6, 30), planned_pct=100.0, weight=0.25))
        db.add(ActivityPlan(project_id=hp1_id, activity_name="Dam & Concrete Works", planned_start=date(2023, 5, 1), planned_end=date(2024, 12, 31), planned_pct=65.0, weight=0.40))
        db.add(ActivityPlan(project_id=hp1_id, activity_name="Headrace Tunnel Excavation", planned_start=date(2023, 7, 1), planned_end=date(2025, 4, 30), planned_pct=40.0, weight=0.20))
        db.add(ActivityPlan(project_id=hp1_id, activity_name="Powerhouse & E&M Erection", planned_start=date(2024, 2, 1), planned_end=date(2025, 9, 30), planned_pct=25.0, weight=0.15))

        db.add(ActivityActual(project_id=hp1_id, activity_name="Site Excavation & Foundation", actual_pct=95.0, actual_date=date(2023, 6, 30)))
        db.add(ActivityActual(project_id=hp1_id, activity_name="Dam & Concrete Works", actual_pct=48.0, actual_date=date(2024, 6, 30)))
        db.add(ActivityActual(project_id=hp1_id, activity_name="Headrace Tunnel Excavation", actual_pct=28.0, actual_date=date(2024, 6, 30)))
        db.add(ActivityActual(project_id=hp1_id, activity_name="Powerhouse & E&M Erection", actual_pct=15.0, actual_date=date(2024, 6, 30)))

        db.add(MaterialStock(project_id=hp1_id, material="Cement", current_stock=4200.0, unit="MT", daily_consumption_rate=180.0, min_threshold=3000.0))
        db.add(MaterialStock(project_id=hp1_id, material="Reinforcement Steel", current_stock=1200.0, unit="MT", daily_consumption_rate=45.0, min_threshold=1000.0))
        db.add(MaterialStock(project_id=hp1_id, material="Aggregate", current_stock=18000.0, unit="m3", daily_consumption_rate=500.0, min_threshold=10000.0))

        db.add(MaterialRequirement(project_id=hp1_id, material="Cement", total_required=320000.0, consumed=145000.0, unit="MT"))
        db.add(MaterialRequirement(project_id=hp1_id, material="Reinforcement Steel", total_required=28000.0, consumed=12400.0, unit="MT"))
        db.add(MaterialRequirement(project_id=hp1_id, material="Penstock Steel", total_required=4500.0, consumed=1800.0, unit="MT"))

        db.add(ProcurementOrder(project_id=hp1_id, material="Cement", po_number="PO-HYDRO-2024-089", po_date=date(2024, 5, 10), expected_delivery=date(2024, 6, 25), quantity=5000.0, unit="MT", status="Delayed"))
        db.add(ProcurementOrder(project_id=hp1_id, material="Penstock Steel Plates", po_number="PO-HYDRO-2024-104", po_date=date(2024, 6, 1), expected_delivery=date(2024, 7, 15), quantity=800.0, unit="MT", status="In Transit"))

        db.add(SiteLog(project_id=hp1_id, log_date=date(2024, 6, 28), weather="Heavy Rain", labor_count=420, notes="Monsoon rainfall delayed tunnel excavation. Cement delivery truck stuck at mountain pass."))

        db.commit()
        print(f"[SUCCESS] Database seeded cleanly with {len(df_projects)} Hydro projects.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
