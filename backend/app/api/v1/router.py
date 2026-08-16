"""API Version 1 Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, deals, documents, financials, health, jobs, organizations, system, valuation

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





