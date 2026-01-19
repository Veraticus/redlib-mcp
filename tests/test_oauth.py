"""
OAuth integration tests.

These tests verify the OAuth flow works with mocked Cloudflare Access responses.
"""

import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient


# Mock OIDC configuration for Cloudflare Access
MOCK_OIDC_CONFIG = {
    "issuer": "https://test-team.cloudflareaccess.com",
    "authorization_endpoint": "https://test-team.cloudflareaccess.com/cdn-cgi/access/sso/oidc/authorize",
    "token_endpoint": "https://test-team.cloudflareaccess.com/cdn-cgi/access/sso/oidc/token",
    "jwks_uri": "https://test-team.cloudflareaccess.com/cdn-cgi/access/certs",
    "response_types_supported": ["code"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
}


@pytest.fixture
def mock_access_config(monkeypatch):
    """Configure Access credentials for testing."""
    monkeypatch.setenv("ACCESS_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ACCESS_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_TEAM_NAME", "test-team")
    monkeypatch.setenv("MCP_SERVER_URL", "http://localhost:8000")


def test_oauth_metadata_endpoint(mock_access_config):
    """Server exposes OAuth discovery metadata."""
    with patch("httpx.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = MOCK_OIDC_CONFIG

        from redlib_mcp import create_authenticated_server

        server = create_authenticated_server()
        app = server.http_app()

        # Use context manager to properly handle ASGI lifespan
        with TestClient(app) as client:
            response = client.get("/.well-known/oauth-authorization-server")

            assert response.status_code == 200
            data = response.json()
            assert "authorization_endpoint" in data
            assert "token_endpoint" in data


def test_protected_endpoint_requires_auth(mock_access_config):
    """MCP endpoints return 401 without valid token."""
    with patch("httpx.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = MOCK_OIDC_CONFIG

        from redlib_mcp import create_authenticated_server

        server = create_authenticated_server()
        app = server.http_app()

        # Use context manager to properly handle ASGI lifespan
        with TestClient(app) as client:
            # Try to access MCP endpoint without auth
            response = client.post("/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})

            assert response.status_code == 401


def test_unauthenticated_server_allows_access(monkeypatch):
    """Server without auth can be created and has no OAuth metadata endpoint."""
    monkeypatch.delenv("ACCESS_CLIENT_ID", raising=False)
    monkeypatch.delenv("ACCESS_CLIENT_SECRET", raising=False)

    from redlib_mcp import create_authenticated_server

    server = create_authenticated_server()
    app = server.http_app()

    # Use context manager to properly handle ASGI lifespan
    with TestClient(app) as client:
        # Without OAuth, the authorization server metadata should not exist
        response = client.get("/.well-known/oauth-authorization-server")

        # Should return 404 when auth is disabled (no OAuth endpoints)
        assert response.status_code == 404
