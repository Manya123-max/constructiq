"""
ConstructIQ – Database connection and SQLAlchemy models.
Uses SQLite for local POC (zero-config). Swap DATABASE_URL for PostgreSQL in production.
"""

import os
from sqlalchemy import (
    create_engine, Column, Text, Float, Integer, Date, DateTime, ForeignKey,
    CheckConstraint, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ─── Connection ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/constructiq.db")

# Ensure data directory exists for SQLite
_db_path = DATABASE_URL.replace("sqlite:///", "")
os.makedirs(os.path.dirname(_db_path), exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Dependency ──────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Models ──────────────────────────────────────────────────────────────────

class ProjectMaster(Base):
    __tablename__ = "project_master"
    project_id            = Column(Text, primary_key=True)
    project_name          = Column(Text, nullable=False)
    project_type          = Column(Text, nullable=False)
    state                 = Column(Text)
    capacity_mw           = Column(Float)
    number_of_units       = Column(Integer)
    commissioning_year    = Column(Integer)
    project_cost_cr       = Column(Float)
    annual_generation_gwh = Column(Float)
    data_completeness     = Column(Float, default=0.0)
    primary_source        = Column(Text)
    created_at            = Column(DateTime, server_default=func.now())

    sources     = relationship("ProjectSource",    back_populates="project")
    hydro_feat  = relationship("HydroFeatures",    back_populates="project", uselist=False)
    thermal_feat= relationship("ThermalFeatures",  back_populates="project", uselist=False)
    materials   = relationship("ProjectMaterial",  back_populates="project")
    equipment   = relationship("ProjectEquipment", back_populates="project")
    cost        = relationship("ProjectCost",      back_populates="project", uselist=False)
    generation  = relationship("ProjectGeneration",back_populates="project")


class ProjectSource(Base):
    __tablename__ = "project_source"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    project_id          = Column(Text, ForeignKey("project_master.project_id"))
    source_name         = Column(Text)
    source_type         = Column(Text)
    document_name       = Column(Text)
    source_url          = Column(Text)
    page_number         = Column(Integer)
    extraction_date     = Column(Date)
    actual_or_estimated = Column(Text, default="actual")
    project             = relationship("ProjectMaster", back_populates="sources")


class HydroFeatures(Base):
    __tablename__ = "hydro_project_features"
    project_id              = Column(Text, ForeignKey("project_master.project_id"), primary_key=True)
    head_m                  = Column(Float)
    design_flow_m3s         = Column(Float)
    dam_height_m            = Column(Float)
    reservoir_volume_mcm    = Column(Float)
    reservoir_area_km2      = Column(Float)
    penstock_length_m       = Column(Float)
    penstock_diameter_m     = Column(Float)
    tunnel_length_m         = Column(Float)
    catchment_area_km2      = Column(Float)
    annual_inflow_mcm       = Column(Float)
    plant_type              = Column(Text)
    turbine_type            = Column(Text)
    unit_capacity_mw        = Column(Float)
    hydraulic_power_mw      = Column(Float)
    capacity_per_head       = Column(Float)
    flow_per_mw             = Column(Float)
    penstock_intensity      = Column(Float)
    dam_height_category     = Column(Text)
    project                 = relationship("ProjectMaster", back_populates="hydro_feat")


class ThermalFeatures(Base):
    __tablename__ = "thermal_project_features"
    project_id              = Column(Text, ForeignKey("project_master.project_id"), primary_key=True)
    fuel_type               = Column(Text)
    coal_hhv_kcal_kg        = Column(Float)
    boiler_efficiency       = Column(Float)
    turbine_efficiency      = Column(Float)
    generator_efficiency    = Column(Float)
    steam_pressure_bar      = Column(Float)
    steam_temperature_c     = Column(Float)
    cooling_type            = Column(Text)
    plant_load_factor       = Column(Float)
    coal_consumption_tpd    = Column(Float)
    water_requirement_m3day = Column(Float)
    steam_flow_tph          = Column(Float)
    boiler_type             = Column(Text)
    unit_capacity_mw        = Column(Float)
    combined_efficiency     = Column(Float)
    coal_tpd_per_mw         = Column(Float)
    water_m3_per_mw         = Column(Float)
    steam_tph_per_mw        = Column(Float)
    project                 = relationship("ProjectMaster", back_populates="thermal_feat")


class ProjectMaterial(Base):
    __tablename__ = "project_materials"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    project_id      = Column(Text, ForeignKey("project_master.project_id"))
    material        = Column(Text, nullable=False)
    quantity        = Column(Float)
    unit            = Column(Text)
    work_category   = Column(Text)
    source_document = Column(Text)
    quantity_per_mw = Column(Float)
    project         = relationship("ProjectMaster", back_populates="materials")


class ProjectEquipment(Base):
    __tablename__ = "project_equipment"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    project_id          = Column(Text, ForeignKey("project_master.project_id"))
    equipment_type      = Column(Text)
    equipment_name      = Column(Text)
    quantity            = Column(Integer)
    capacity_per_unit   = Column(Float)
    technology          = Column(Text)
    source              = Column(Text)
    project             = relationship("ProjectMaster", back_populates="equipment")


class ProjectCost(Base):
    __tablename__ = "project_cost"
    project_id              = Column(Text, ForeignKey("project_master.project_id"), primary_key=True)
    civil_cost_cr           = Column(Float)
    equipment_cost_cr       = Column(Float)
    material_cost_cr        = Column(Float)
    em_works_cr             = Column(Float)
    hydromech_cost_cr       = Column(Float)
    other_cost_cr           = Column(Float)
    total_cost_cr           = Column(Float)
    cost_year               = Column(Integer)
    cpi_index               = Column(Float, default=1.0)
    cost_normalized_2024_cr = Column(Float)
    project                 = relationship("ProjectMaster", back_populates="cost")


class ProjectGeneration(Base):
    __tablename__ = "project_generation"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    project_id      = Column(Text, ForeignKey("project_master.project_id"))
    year            = Column(Integer)
    generation_gwh  = Column(Float)
    capacity_factor = Column(Float)
    availability    = Column(Float)
    inflow_mcm      = Column(Float)
    fuel_consumption= Column(Float)
    source          = Column(Text)
    project         = relationship("ProjectMaster", back_populates="generation")


# ─── Monitoring Tables ───────────────────────────────────────────────────────
class ActivityPlan(Base):
    __tablename__ = "activity_plan"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    project_id      = Column(Text)
    activity_name   = Column(Text)
    planned_start   = Column(Date)
    planned_end     = Column(Date)
    planned_pct     = Column(Float)
    weight          = Column(Float, default=1.0)


class ActivityActual(Base):
    __tablename__ = "activity_actual"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    project_id      = Column(Text)
    activity_name   = Column(Text)
    actual_pct      = Column(Float)
    actual_date     = Column(Date)
    updated_at      = Column(DateTime, server_default=func.now())


class MaterialStock(Base):
    __tablename__ = "material_stock"
    id                      = Column(Integer, primary_key=True, autoincrement=True)
    project_id              = Column(Text)
    material                = Column(Text)
    current_stock           = Column(Float)
    unit                    = Column(Text)
    daily_consumption_rate  = Column(Float)
    min_threshold           = Column(Float)
    updated_at              = Column(DateTime, server_default=func.now())


class MaterialRequirement(Base):
    __tablename__ = "material_requirement"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    project_id      = Column(Text)
    material        = Column(Text)
    total_required  = Column(Float)
    consumed        = Column(Float, default=0)
    unit            = Column(Text)


class ProcurementOrder(Base):
    __tablename__ = "procurement_orders"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    project_id          = Column(Text)
    material            = Column(Text)
    po_number           = Column(Text)
    po_date             = Column(Date)
    expected_delivery   = Column(Date)
    quantity            = Column(Float)
    unit                = Column(Text)
    status              = Column(Text, default="Open")


class SiteLog(Base):
    __tablename__ = "site_logs"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    project_id  = Column(Text)
    log_date    = Column(Date)
    weather     = Column(Text)
    labor_count = Column(Integer)
    notes       = Column(Text)


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created.")


if __name__ == "__main__":
    create_tables()
