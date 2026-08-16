"""Tests for Global Error Handling and Domain Exceptions."""

import pytest
from httpx import AsyncClient
from fastapi import APIRouter
from app.core.exceptions import NotFoundException, ForbiddenException
from app.main import app

# Temporary test router for exception triggers
error_router = APIRouter(prefix="/api/v1/test-errors", tags=["Test Errors"])


@error_router.get("/not-found")
async def trigger_not_found():
    raise NotFoundException(resource="Deal", resource_id="deal-999")


@error_router.get("/forbidden")
async def trigger_forbidden():
    raise ForbiddenException("User lacks clearance for this transaction room.")


app.include_router(error_router)


@pytest.mark.asyncio
async def test_not_found_exception_handling(async_client: AsyncClient):
    """Verify NotFoundException formats standardized JSON response."""
    response = await async_client.get("/api/v1/test-errors/not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
    assert "Deal with identifier 'deal-999' was not found" in data["error"]["message"]


@pytest.mark.asyncio
async def test_forbidden_exception_handling(async_client: AsyncClient):
    """Verify ForbiddenException formats standardized JSON response."""
    response = await async_client.get("/api/v1/test-errors/forbidden")
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"
