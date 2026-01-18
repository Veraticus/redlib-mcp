import pytest
import httpx
from unittest.mock import AsyncMock, patch


def make_response(status_code: int, json_data: dict) -> httpx.Response:
    """Create a properly configured httpx.Response for testing."""
    request = httpx.Request("GET", "http://test.com")
    return httpx.Response(status_code, json=json_data, request=request)


@pytest.mark.asyncio
async def test_client_get_success():
    from redlib_mcp import RedlibClient

    client = RedlibClient("http://localhost:8080")

    mock_response = make_response(200, {"data": {"posts": []}, "error": None})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        result = await client.get("/r/rust")

    assert result == {"data": {"posts": []}, "error": None}


@pytest.mark.asyncio
async def test_client_appends_js_extension():
    from redlib_mcp import RedlibClient

    client = RedlibClient("http://localhost:8080")

    mock_response = make_response(200, {"data": None, "error": None})
    mock_get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.get", mock_get):
        await client.get("/r/rust")

    # Check that .js was appended
    call_url = mock_get.call_args[0][0]
    assert call_url == "http://localhost:8080/r/rust.js"


@pytest.mark.asyncio
async def test_client_strips_trailing_slash_from_base():
    from redlib_mcp import RedlibClient

    client = RedlibClient("http://localhost:8080/")

    mock_response = make_response(200, {"data": None, "error": None})
    mock_get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.get", mock_get):
        await client.get("/r/rust")

    call_url = mock_get.call_args[0][0]
    assert call_url == "http://localhost:8080/r/rust.js"


@pytest.mark.asyncio
async def test_client_passes_query_params():
    from redlib_mcp import RedlibClient

    client = RedlibClient("http://localhost:8080")

    mock_response = make_response(200, {"data": None, "error": None})
    mock_get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.get", mock_get):
        await client.get("/r/rust", params={"sort": "new", "after": "abc123"})

    call_kwargs = mock_get.call_args[1]
    assert call_kwargs["params"] == {"sort": "new", "after": "abc123"}
