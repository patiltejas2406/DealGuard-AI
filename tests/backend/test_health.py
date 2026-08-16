"""Tests for Health & System Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_liveness(async_client: AsyncClient):
    """Verify that the /api/v1/health liveness probe returns HTTP 200."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "DealGuard AI"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_system_info(async_client: AsyncClient):
    """Verify that /api/v1/system/info returns architecture capabilities and frozen specifications."""
    response = await async_client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "DealGuard AI"
    assert data["architecture"]["type"] == "Modular Monolith"
    assert data["architecture"]["deterministic_financial_engine"] is True
    assert data["ai_spec"]["embedding_dimension"] == 1536
    assert data["security"]["password_hasher"] == "Argon2id"


@pytest.mark.asyncio
async def test_request_id_and_timing_headers(async_client: AsyncClient):
    """Verify observability middleware sets tracing and timing headers."""
    response = await async_client.get("/api/v1/health")
    assert "x-request-id" in response.headers
    assert "x-process-time-ms" in response.headers
