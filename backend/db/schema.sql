-- ConstructIQ Database Schema
-- All power plant project data, materials, equipment, generation and cost

-- ─────────────────────────────────────────
-- 1. PROJECT MASTER
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_master (
    project_id            TEXT PRIMARY KEY,
    project_name          TEXT NOT NULL,
    project_type          TEXT NOT NULL CHECK (project_type IN ('hydro', 'thermal')),
    state                 TEXT,
    capacity_mw           FLOAT,
    number_of_units       INTEGER,
    commissioning_year    INTEGER,
    project_cost_cr       FLOAT,
    annual_generation_gwh FLOAT,
    data_completeness     FLOAT DEFAULT 0.0,
    primary_source        TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────
-- 2. PROJECT SOURCE (Provenance / Audit)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_source (
    id                  SERIAL PRIMARY KEY,
    project_id          TEXT REFERENCES project_master(project_id),
    source_name         TEXT,   -- 'CEA', 'PARIVESH', 'eTenders', 'data.gov.in'
    source_type         TEXT,   -- 'Government' | 'PSU' | 'International'
    document_name       TEXT,
    source_url          TEXT,
    page_number         INTEGER,
    extraction_date     DATE,
    actual_or_estimated TEXT DEFAULT 'actual'  -- 'actual' | 'estimated' | 'design'
);

-- ─────────────────────────────────────────
-- 3. HYDRO PROJECT FEATURES
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS hydro_project_features (
    project_id              TEXT PRIMARY KEY REFERENCES project_master(project_id),
    -- Raw features
    head_m                  FLOAT,
    design_flow_m3s         FLOAT,
    dam_height_m            FLOAT,
    reservoir_volume_mcm    FLOAT,
    reservoir_area_km2      FLOAT,
    penstock_length_m       FLOAT,
    penstock_diameter_m     FLOAT,
    tunnel_length_m         FLOAT,
    catchment_area_km2      FLOAT,
    annual_inflow_mcm       FLOAT,
    plant_type              TEXT,  -- 'run-of-river' | 'storage' | 'pumped'
    turbine_type            TEXT,  -- 'Francis' | 'Pelton' | 'Kaplan'
    -- Engineered features (computed, never direct ML input for same target)
    unit_capacity_mw        FLOAT,
    hydraulic_power_mw      FLOAT,
    capacity_per_head       FLOAT,
    flow_per_mw             FLOAT,
    penstock_intensity      FLOAT,
    dam_height_category     TEXT   -- 'Low' | 'Medium' | 'High' | 'VeryHigh'
);

-- ─────────────────────────────────────────
-- 4. THERMAL PROJECT FEATURES
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS thermal_project_features (
    project_id              TEXT PRIMARY KEY REFERENCES project_master(project_id),
    -- Raw features
    fuel_type               TEXT,
    coal_hhv_kcal_kg        FLOAT,
    boiler_efficiency       FLOAT,
    turbine_efficiency      FLOAT,
    generator_efficiency    FLOAT,
    steam_pressure_bar      FLOAT,
    steam_temperature_c     FLOAT,
    cooling_type            TEXT,
    plant_load_factor       FLOAT,
    coal_consumption_tpd    FLOAT,
    water_requirement_m3day FLOAT,
    steam_flow_tph          FLOAT,
    boiler_type             TEXT,
    -- Engineered features
    unit_capacity_mw        FLOAT,
    combined_efficiency     FLOAT,
    coal_tpd_per_mw         FLOAT,
    water_m3_per_mw         FLOAT,
    steam_tph_per_mw        FLOAT
);

-- ─────────────────────────────────────────
-- 5. PROJECT MATERIALS (Long format)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_materials (
    id              SERIAL PRIMARY KEY,
    project_id      TEXT REFERENCES project_master(project_id),
    material        TEXT NOT NULL,
    quantity        FLOAT,
    unit            TEXT,
    work_category   TEXT,  -- 'Civil' | 'Structural' | 'Mechanical' | 'Electrical'
    source_document TEXT,
    quantity_per_mw FLOAT  -- intensity (validation/benchmarking only)
);

-- ─────────────────────────────────────────
-- 6. PROJECT EQUIPMENT
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_equipment (
    id                  SERIAL PRIMARY KEY,
    project_id          TEXT REFERENCES project_master(project_id),
    equipment_type      TEXT,
    equipment_name      TEXT,
    quantity            INTEGER,
    capacity_per_unit   FLOAT,
    technology          TEXT,
    source              TEXT
);

-- ─────────────────────────────────────────
-- 7. PROJECT COST
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_cost (
    project_id              TEXT PRIMARY KEY REFERENCES project_master(project_id),
    civil_cost_cr           FLOAT,
    equipment_cost_cr       FLOAT,
    material_cost_cr        FLOAT,
    em_works_cr             FLOAT,
    hydromech_cost_cr       FLOAT,
    other_cost_cr           FLOAT,
    total_cost_cr           FLOAT,
    cost_year               INTEGER,
    cpi_index               FLOAT DEFAULT 1.0,
    cost_normalized_2024_cr FLOAT
);

-- ─────────────────────────────────────────
-- 8. PROJECT GENERATION
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_generation (
    id                  SERIAL PRIMARY KEY,
    project_id          TEXT REFERENCES project_master(project_id),
    year                INTEGER,
    generation_gwh      FLOAT,
    capacity_factor     FLOAT,
    availability        FLOAT,
    inflow_mcm          FLOAT,
    fuel_consumption    FLOAT,
    source              TEXT
);

-- ─────────────────────────────────────────
-- MONITORING TABLES (Mock for POC)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activity_plan (
    id                  SERIAL PRIMARY KEY,
    project_id          TEXT,
    activity_name       TEXT,
    planned_start       DATE,
    planned_end         DATE,
    planned_pct         FLOAT,
    weight              FLOAT DEFAULT 1.0  -- for weighted progress
);

CREATE TABLE IF NOT EXISTS activity_actual (
    id                  SERIAL PRIMARY KEY,
    project_id          TEXT,
    activity_name       TEXT,
    actual_pct          FLOAT,
    actual_date         DATE,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS material_stock (
    id                      SERIAL PRIMARY KEY,
    project_id              TEXT,
    material                TEXT,
    current_stock           FLOAT,
    unit                    TEXT,
    daily_consumption_rate  FLOAT,
    min_threshold           FLOAT,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS material_requirement (
    id              SERIAL PRIMARY KEY,
    project_id      TEXT,
    material        TEXT,
    total_required  FLOAT,
    consumed        FLOAT DEFAULT 0,
    unit            TEXT
);

CREATE TABLE IF NOT EXISTS procurement_orders (
    id                  SERIAL PRIMARY KEY,
    project_id          TEXT,
    material            TEXT,
    po_number           TEXT,
    po_date             DATE,
    expected_delivery   DATE,
    quantity            FLOAT,
    unit                TEXT,
    status              TEXT DEFAULT 'Open'
);

CREATE TABLE IF NOT EXISTS site_logs (
    id              SERIAL PRIMARY KEY,
    project_id      TEXT,
    log_date        DATE,
    weather         TEXT,
    labor_count     INTEGER,
    notes           TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_materials_project ON project_materials(project_id);
CREATE INDEX IF NOT EXISTS idx_equipment_project ON project_equipment(project_id);
CREATE INDEX IF NOT EXISTS idx_generation_project ON project_generation(project_id);
CREATE INDEX IF NOT EXISTS idx_source_project ON project_source(project_id);
CREATE INDEX IF NOT EXISTS idx_activity_plan_project ON activity_plan(project_id);
CREATE INDEX IF NOT EXISTS idx_activity_actual_project ON activity_actual(project_id);
CREATE INDEX IF NOT EXISTS idx_material_stock_project ON material_stock(project_id);
CREATE INDEX IF NOT EXISTS idx_procurement_project ON procurement_orders(project_id);
