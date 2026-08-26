"""API Version 1 Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    decision,
    deals,
    documents,
    financials,
    health,
    integration,
    jobs,
    legal,
    organizations,
    risk,
    scenarios,
    synergies,
    system,
    valuation,
)

api_router = APIRouter()

# Core Monitoring & System Endpoints
api_router.include_router(health.router)
api_router.include_router(system.router)

# Authentication & Session Management
api_router.include_router(auth.router)

# Domain Endpoints
api_router.include_router(organizations.router)
api_router.include_router(deals.router)
api_router.include_router(documents.router)
api_router.include_router(jobs.router)
api_router.include_router(financials.router)
api_router.include_router(valuation.router)
api_router.include_router(risk.router)
api_router.include_router(decision.router)
api_router.include_router(scenarios.router)
api_router.include_router(synergies.router)
api_router.include_router(integration.router)
api_router.include_router(legal.router)





