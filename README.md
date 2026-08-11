# ConstructIQ — Power Plant AI Agent System

> POC: Hydro + Thermal plant estimation using ML + RAG backed by government data sources (CEA, PARIVESH, eProcurement, data.gov.in)

## Quick Start

### 1. Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Step 1: Generate synthetic training data
python data_pipeline\generate_synthetic_data.py

# Step 2: Seed database
python data_pipeline\seed_database.py

# Step 3: Train ML models
python ml\train_models.py

# Step 4: Ingest documents into ChromaDB (RAG)
python rag\vector_store.py

# Step 5: Start API server
python main.py
# API will be running at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 2. Frontend Setup

```powershell
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:5173
```

## Architecture

```
constructiq/
├── backend/
│   ├── agents/
│   │   ├── estimation/     ← orchestrator.py (LangGraph-style pipeline)
│   │   └── monitoring/     ← agents.py (5 monitoring agents)
│   ├── rag/                ← ChromaDB vector store + retriever
│   ├── ml/
│   │   ├── features/       ← hydro_features.py, thermal_features.py
│   │   ├── models/         ← trained .joblib files
│   │   └── train_models.py ← XGBoost + GradBoost training
│   ├── data_pipeline/      ← data generation and seeding
│   ├── db/                 ← SQLAlchemy models + schema
│   └── main.py             ← FastAPI app
└── frontend/
    └── src/
        ├── components/
        │   ├── ProjectForm.jsx
        │   ├── EstimationPanel.jsx
        │   └── MonitoringDashboard.jsx
        ├── api/client.js
        └── store/useStore.js
```

## Data Sources (Government / Official)

| Source | Role |
|---|---|
| CEA (cea.nic.in) | Project cost, technical data, DPRs |
| PARIVESH | Environmental clearance documents, material quantities |
| data.gov.in | Installed capacity, generation statistics |
| eProcurement (etenders.gov.in) | BOQ Excel files |
| IEA | Generation benchmarks, capacity factors |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/estimate | Full project estimation |
| GET | /api/monitor/{id}/status | Agent 1: Project status |
| GET | /api/monitor/{id}/delays | Agent 2: Delay detection |
| GET | /api/monitor/{id}/rootcause | Agent 3: Root cause |
| GET | /api/monitor/{id}/materials | Agent 4: Material availability |
| GET | /api/monitor/{id}/procurement | Agent 5: Procurement risk |
| GET | /api/projects | List all projects |

## ML Models

| Model | Algorithm | Data | Targets |
|---|---|---|---|
| Hydro Material | XGBoost MultiOutput | 25 projects | concrete, cement, steel, aggregate |
| Thermal Material | XGBoost MultiOutput | 20 projects | concrete, cement, steel, piping |
| Hydro Generation | XGBoost | project features | annual GWh, capacity factor |
| Thermal Generation | XGBoost | project features | annual GWh |
| Hydro Cost | GradientBoosting | project + materials | civil, equipment, total cost |
| Thermal Cost | GradientBoosting | project + materials | civil, equipment, total cost |
