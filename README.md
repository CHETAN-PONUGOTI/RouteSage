# Safiri Route Intelligence

An explainable, multi-objective shipment route decision platform.

## Overview
Safiri Route Intelligence is a decision-support system designed to help logistics planners evaluate and select optimal shipment routes under competing objectives and uncertainty. By balancing **Cost**, **Transit Time**, **Reliability**, and **Risk**, the platform recommends the best route and provides an evidence-based explanation for its decision. 

This repository was created as an assignment submission. It prioritizes deterministic reliability, explainability, and algorithmic transparency over black-box AI recommendations. 

---

## 🏗 Architecture & Technology Stack

**Frontend**: Next.js 14 (App Router), React, Tailwind CSS, shadcn/ui, Jest  
**Backend**: Python 3.11+, FastAPI, Pydantic, SQLAlchemy, Alembic, Pytest  
**AI/LLM**: Google Gemini SDK (`google-genai`), restricted to explanation generation.  
**Database**: SQLite (Default for development/evaluation) / PostgreSQL (Supported via SQLAlchemy)

**Core Principle: "The optimizer decides. The LLM explains."**
The system uses a strictly deterministic algorithm to score, filter, and rank routes. The LLM only receives verified output (frozen Pydantic schemas) to generate natural language explanations. It has no authority to alter recommendations or feasibility.

---

## 🚀 Setup & Execution

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv:
# Windows: venv\Scripts\activate 
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

**Environment Variables**
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Inside `.env`, configure your Gemini API Key if you want LLM explanations:
```env
GEMINI_API_KEY=<your-api-key>
ENABLE_LLM_EXPLANATION=true
```
*(If the key is missing or disabled, the system gracefully falls back to deterministic explanations).*

**Database Setup & Migrations**
By default, the system uses a local SQLite database (`test_safiri.db`). Run migrations to initialize the schema:
```bash
alembic upgrade head
```
*(Optional: For PostgreSQL, run `docker-compose up -d db` and set `DATABASE_URL=postgresql://safiri:safiripassword@localhost:5432/safiri_db`).*

**Seed Demo Data**
Populate the database with the verified synthetic dataset (30 shipments, 120 candidate routes):
```bash
python scripts/seed_database.py
```
*Expected output: `Successfully seeded 30 shipments and 120 candidate routes into the database.`*

**Start the API Server**
```bash
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs` and Health Check at `http://localhost:8000/health`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The UI will be available at `http://localhost:3000`.

**Verify the Demo in Browser:**
1. Open `http://localhost:3000/shipments` to view the 30 seeded shipments.
2. Select any shipment to view its 4 candidate routes.
3. Click **"Evaluate Routes"** (`/shipments/{shipmentId}/evaluate`) and click **"Run Optimization"** to view the winning recommendation, multi-attribute score breakdown, Pareto trade-off badges, and the explanation card.

---

## 🧪 Testing & Evaluation

### Running Tests
The project features comprehensive test coverage.
**Backend**:
```bash
cd backend
pytest -v
```
**Frontend**:
```bash
cd frontend
npm run test
```

### Running the Decision-System Evaluation
To evaluate the deterministic optimizer's behavior mathematically against a synthetic dataset (30 shipments, 120 routes), run:
```bash
cd backend
python scripts/evaluate_decision_system.py
```
This script measures feasibility rates, recommendation distributions, Pareto-efficiency overlap, and verifies the deterministic repeatability of the engine.

---

## 🧠 Optimization Engine Deep Dive

The route evaluation pipeline follows a strict, multi-stage deterministic process:

### 1. Hard Constraints Engine
Routes are immediately marked **infeasible** if they violate hard constraints, such as:
- Max allowable transit time (`delivery_deadline`)
- Cost exceeding shipment value limits
- Unacceptable risk categorizations

### 2. Soft Constraints & Normalization
Feasible routes are scored across four dimensions: **Cost**, **Time**, **Reliability**, and **Risk**.
Since these values use completely different units (dollars vs. hours vs. percentages), the engine uses Min-Max normalization to map all metrics to a `[0.0, 1.0]` scale (where 1.0 is always the most desirable).

### 3. Weighted Objectives & Ranking
The normalized scores are multiplied by the user's defined **Optimization Profile** (e.g., 40% Cost, 30% Time, 20% Reliability, 10% Risk) to compute a final Weighted Score. The feasible route with the highest score is recommended.

### 4. Pareto Analysis
The engine identifies the **Pareto Frontier**—routes where no other route is strictly better in all dimensions. This guarantees that alternative recommendations (trade-offs) presented to the user are mathematically optimal under different potential weights.

### 5. Sensitivity Analysis
The pipeline perturbs the user's weights by ±20% to test stability. If the recommended route changes under slight weight variations, the platform flags the recommendation as "Highly Sensitive", warning the planner.

---

## 🤖 Explanation Layer (Gemini)

When a route is selected, the platform must explain *why*.

1. **Evidence Collection**: The `EvidenceBuilder` curates a strict, frozen summary of the `OptimizationResult` (feasibility, normalized score contributions, constraint violations, and Pareto status).
2. **LLM Generation**: Gemini receives a strictly constructed prompt outlining the evidence.
3. **Structured Grounding**: The LLM is forced to return a JSON schema (`StructuredExplanation`). 
4. **Validation**: The backend parses the JSON and performs **Grounding Validation**. If Gemini hallucinates an unknown route, contradicts feasibility, or names the wrong recommended route, the system throws a `GroundingError` and immediately falls back to a deterministic string generator.

---

## ⚠️ Known Limitations
- **Geospatial Realism**: The synthetic data generator creates abstract routes and distances. Real-world implementation would require integration with map APIs (e.g., Google Maps, Mapbox) for physical routing paths.
- **LLM Nuance**: While the grounding engine prevents factual contradictions regarding recommendations and feasibility, numeric assertions within the LLM's free-text `reasons` arrays are not strictly audited by NLP extraction. 
- **Scale**: The current `RouteOptimizer` loads alternatives into memory. For true enterprise scale with millions of nodes, the optimization would need to be translated into a mathematical solver (e.g., OR-Tools, CPLEX) before applying multi-criteria scoring.
