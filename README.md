# DealGuard AI

> **AI-Powered M&A Due Diligence, Deal Intelligence & Post-Deal Value Creation Platform**

---

## 1. Overview
DealGuard AI is an institutional-grade decision intelligence platform that transforms raw M&A due diligence packets (P&Ls, balance sheets, SEC filings, supplier/customer contracts, debt schedules) into verified financial metrics, explainable 17-pillar risk assessments, deterministic valuations (DCF & CCA), interactive what-if deal simulations, and post-merger 100-day value creation roadmaps.

---

## 2. Architecture Highlights
- **Deterministic Domain Engine**: All calculations (EBITDA, Net Debt, CAGR, WACC, DCF, Multiples, Sensitivity Heatmaps, What-If Deltas) are computed by pure-Python domain services.
- **Evidence-First RAG & LangGraph**: AI reasoning is grounded in character-level document citations (`doc_id`, `page_number`, `exact_quote`).
- **PostgreSQL 16 + pgvector**: Unified relational ACID storage and vector embeddings (`vector(1536)`).
- **Celery + Redis**: Resilient asynchronous background pipeline for document parsing, OCR, table normalization, and embedding jobs.
- **Security & Multi-Tenancy**: Tenant-isolated boundaries, deal-level RBAC, Argon2id password hashing, and encrypted object storage.

---

## 3. Repository Structure
```
DealGuard AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints & routers
│   │   ├── core/            # Config, security, logging, exceptions, database
│   │   ├── domains/         # Domain business logic & services
│   │   │   ├── auth/        # Authentication & RBAC
│   │   │   ├── deals/       # Deal lifecycle management
│   │   │   ├── documents/   # Ingestion, parsing & storage
│   │   │   ├── financials/  # 3-Statement & ratio calculations
│   │   │   ├── valuation/   # DCF, CCA & Sensitivity engines
│   │   │   ├── risk/        # 17-Pillar risk scoring model
│   │   │   ├── scenarios/   # What-if simulation engine
│   │   │   ├── post_deal/   # BU Matrix & 100-day execution
│   │   │   ├── ai/          # Embeddings, LangGraph & RAG
│   │   │   └── audit/       # Immutable audit logs & overrides
│   │   └── main.py          # FastAPI application factory
│   ├── alembic/             # Database migrations
│   ├── Dockerfile           # Backend container
│   ├── pyproject.toml       # Python package metadata
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js 14 App Router pages
│   │   ├── components/      # UI & Layout components
│   │   ├── lib/             # API client & utilities
│   │   └── types/           # TypeScript interface contracts
│   ├── package.json         # Node dependencies
│   ├── tsconfig.json        # TypeScript configuration
│   └── Dockerfile           # Frontend container
├── infra/
│   └── docker-compose.yml   # Local development stack
├── docs/                    # Architecture & ADR documentation
├── scripts/                 # Dev, test & seed helper scripts
├── tests/                   # Backend & frontend automated test suite
└── .env.example             # Environment variable template
```

---

## 4. Quickstart Guide (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+ (Node 20 LTS recommended)
- Docker & Docker Compose (optional for full containerized stack)

### 1. Environment Setup
```bash
cp .env.example .env
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend health check: `http://localhost:8000/api/v1/health`  
Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 3. Database Migrations & Seeding
```bash
# Apply migrations
cd backend && alembic upgrade head

# Seed 3 core synthetic deals (ApexCloud, TitanPrecision, MedVance)
cd .. && ./scripts/seed.sh
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend Web App: `http://localhost:3000`

### 5. Running Full Test Suite
```bash
./scripts/test.sh
```

### 6. Running Full Stack via Docker
```bash
docker-compose -f infra/docker-compose.yml up -d
```

