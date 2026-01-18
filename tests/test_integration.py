"""
Integration tests - require a running Redlib instance.
Skip if REDLIB_URL is not set or instance is unavailable.
"""

import json
import os
import pytest
import httpx


# Skip all tests if no Redlib URL configured
pytestmark = pytest.mark.skipif(
    not os.getenv("REDLIB_URL"),
    reason="REDLIB_URL not set - skipping integration tests"
)


@pytest.fixture
def redlib_available():
    """Check if Redlib is actually reachable."""
    url = os.getenv("REDLIB_URL", "http://localhost:8080")
    try:
        response = httpx.get(f"{url}/r/all.js", timeout=5)
        return response.status_code == 200
    except httpx.RequestError:
        return False


@pytest.mark.asyncio
async def test_get_subreddit_integration(redlib_available):
    if not redlib_available:
        pytest.skip("Redlib not reachable")

    from redlib_mcp import get_subreddit, init_client
    init_client()

    result = json.loads(await get_subreddit("all"))

    assert result.get("error") is None
    assert result.get("data") is not None
    assert "posts" in result["data"]
