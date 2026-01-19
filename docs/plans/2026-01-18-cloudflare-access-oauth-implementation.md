# Cloudflare Access OAuth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add OAuth 2.0 authentication to redlib-mcp using Cloudflare Access as the OIDC provider.

**Architecture:** Use FastMCP's built-in `OIDCProxy` which handles all OAuth complexity. The server acts as an OAuth provider to MCP clients while delegating authentication to Cloudflare Access. MCP tools remain unchanged.

**Tech Stack:** fastmcp (replaces mcp), uvicorn (ASGI server)

---

## Task 1: Update Dependencies

**Files:**
- Modify: `pyproject.toml`
- Modify: `flake.nix` (if it pins dependencies)

**Step 1: Update pyproject.toml**

Replace `mcp>=1.5.0` with `fastmcp>=2.13.0` and add `uvicorn`:

```toml
[project]
name = "redlib-mcp"
version = "0.1.0"
description = "MCP server for Redlib - privacy-focused Reddit frontend"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.13.0",
    "httpx>=0.27.0",
    "uvicorn>=0.30.0",
]

[project.scripts]
redlib-mcp = "redlib_mcp:main"
redlib-mcp-server = "redlib_mcp:main_server"
```

**Step 2: Check flake.nix for dependency pins**

If flake.nix pins mcp, update it to fastmcp.

**Step 3: Verify installation**

Run: `nix develop --command pip list | grep -i fastmcp`
Expected: `fastmcp` version 2.13.0+

**Step 4: Commit**

```bash
git add pyproject.toml flake.nix
git commit -m "deps: switch from mcp to fastmcp for OAuth support"
```

---

## Task 2: Update Imports in redlib_mcp.py

**Files:**
- Modify: `src/redlib_mcp.py`

**Step 1: Update FastMCP import**

Change:
```python
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
```

To:
```python
from fastmcp import FastMCP
```

Note: `TransportSecuritySettings` is not needed with fastmcp - it handles security differently.

**Step 2: Simplify server initialization**

Remove the transport security configuration since fastmcp handles this via auth:

```python
server = FastMCP("redlib-mcp")
```

**Step 3: Run tests to verify tools still work**

Run: `nix develop --command pytest tests/ -v`
Expected: All existing tests pass

**Step 4: Commit**

```bash
git add src/redlib_mcp.py
git commit -m "refactor: update imports from mcp to fastmcp"
```

---

## Task 3: Add Access Configuration Loading

**Files:**
- Modify: `src/redlib_mcp.py`

**Step 1: Write test for config loading**

Create test in `tests/test_config.py`:

```python
def test_load_access_config_from_env(monkeypatch):
    """Access config loads from environment variables."""
    monkeypatch.setenv("ACCESS_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ACCESS_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_TEAM_NAME", "test-team")

    from redlib_mcp import load_access_config
    config = load_access_config()

    assert config["client_id"] == "test-client-id"
    assert config["client_secret"] == "test-secret"
    assert config["config_url"] == "https://test-team.cloudflareaccess.com/cdn-cgi/access/sso/oidc/.well-known/openid-configuration"


def test_load_access_config_missing_returns_none(monkeypatch):
    """Missing Access config returns None (auth disabled)."""
    monkeypatch.delenv("ACCESS_CLIENT_ID", raising=False)
    monkeypatch.delenv("ACCESS_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("ACCESS_TEAM_NAME", raising=False)

    from redlib_mcp import load_access_config
    config = load_access_config()

    assert config is None


def test_load_access_config_custom_urls(monkeypatch):
    """Custom Access URLs override defaults."""
    monkeypatch.setenv("ACCESS_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ACCESS_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_CONFIG_URL", "https://custom.example.com/.well-known/openid-configuration")

    from redlib_mcp import load_access_config
    config = load_access_config()

    assert config["config_url"] == "https://custom.example.com/.well-known/openid-configuration"
```

**Step 2: Run test to verify it fails**

Run: `nix develop --command pytest tests/test_config.py::test_load_access_config_from_env -v`
Expected: FAIL with "cannot import name 'load_access_config'"

**Step 3: Implement load_access_config**

Add to `src/redlib_mcp.py` after `load_config()`:

```python
def load_access_config() -> dict | None:
    """
    Load Cloudflare Access configuration for OAuth.

    Returns None if not configured (auth disabled).

    Environment variables:
        ACCESS_CLIENT_ID: OAuth client ID from Access
        ACCESS_CLIENT_SECRET: OAuth client secret from Access
        ACCESS_TEAM_NAME: Cloudflare team name (used to construct URLs)
        ACCESS_CONFIG_URL: Optional custom OIDC config URL
    """
    client_id = os.getenv("ACCESS_CLIENT_ID")
    client_secret = os.getenv("ACCESS_CLIENT_SECRET")

    # Auth disabled if credentials not provided
    if not client_id or not client_secret:
        return None

    # Build OIDC config URL
    config_url = os.getenv("ACCESS_CONFIG_URL")
    if not config_url:
        team_name = os.getenv("ACCESS_TEAM_NAME")
        if not team_name:
            logger.warning("ACCESS_TEAM_NAME not set, cannot construct OIDC URL")
            return None
        config_url = f"https://{team_name}.cloudflareaccess.com/cdn-cgi/access/sso/oidc/.well-known/openid-configuration"

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "config_url": config_url,
    }
```

**Step 4: Run tests to verify they pass**

Run: `nix develop --command pytest tests/test_config.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_config.py
git commit -m "feat: add Cloudflare Access configuration loading"
```

---

## Task 4: Create HTTP Server Entry Point

**Files:**
- Modify: `src/redlib_mcp.py`

**Step 1: Write test for server creation with auth**

Add to `tests/test_config.py`:

```python
def test_create_server_with_auth(monkeypatch):
    """Server created with OIDCProxy when Access configured."""
    monkeypatch.setenv("ACCESS_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ACCESS_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_TEAM_NAME", "test-team")
    monkeypatch.setenv("MCP_SERVER_URL", "http://localhost:8000")

    # This test just verifies the server can be created without error
    # Full OAuth flow requires integration testing
    from redlib_mcp import create_authenticated_server
    server = create_authenticated_server()

    assert server is not None
    assert server.name == "redlib-mcp"


def test_create_server_without_auth(monkeypatch):
    """Server created without auth when Access not configured."""
    monkeypatch.delenv("ACCESS_CLIENT_ID", raising=False)
    monkeypatch.delenv("ACCESS_CLIENT_SECRET", raising=False)

    from redlib_mcp import create_authenticated_server
    server = create_authenticated_server()

    assert server is not None
```

**Step 2: Run test to verify it fails**

Run: `nix develop --command pytest tests/test_config.py::test_create_server_with_auth -v`
Expected: FAIL with "cannot import name 'create_authenticated_server'"

**Step 3: Implement create_authenticated_server and main_server**

Add to `src/redlib_mcp.py`:

```python
from fastmcp.server.auth.oidc_proxy import OIDCProxy


def create_authenticated_server() -> FastMCP:
    """
    Create MCP server with optional OAuth authentication.

    If Access is configured, returns server with OIDCProxy auth.
    Otherwise, returns unauthenticated server.
    """
    access_config = load_access_config()

    if access_config:
        base_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        auth = OIDCProxy(
            config_url=access_config["config_url"],
            client_id=access_config["client_id"],
            client_secret=access_config["client_secret"],
            base_url=base_url,
        )
        logger.info(f"OAuth enabled via Cloudflare Access")
        return FastMCP("redlib-mcp", auth=auth)
    else:
        logger.info("OAuth disabled - no Access credentials configured")
        return FastMCP("redlib-mcp")


def main_server():
    """HTTP server entry point with OAuth support."""
    init_client()

    # Create server with auth
    auth_server = create_authenticated_server()

    # Copy tools from the global server to auth server
    # (Tools are registered on the module-level server instance)
    for tool_name, tool_func in server._tool_manager._tools.items():
        auth_server._tool_manager._tools[tool_name] = tool_func

    # Run HTTP server
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))

    auth_server.run(transport="http", host=host, port=port)
```

**Step 4: Run tests**

Run: `nix develop --command pytest tests/test_config.py -v`
Expected: All pass

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_config.py
git commit -m "feat: add HTTP server entry point with OAuth support"
```

---

## Task 5: Update Entry Point in pyproject.toml

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add redlib-mcp-server entry point**

Ensure pyproject.toml has:

```toml
[project.scripts]
redlib-mcp = "redlib_mcp:main"
redlib-mcp-server = "redlib_mcp:main_server"
```

**Step 2: Reinstall package**

Run: `nix develop --command pip install -e .`
Expected: Both entry points available

**Step 3: Verify entry points**

Run: `nix develop --command which redlib-mcp-server`
Expected: Path to installed script

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add redlib-mcp-server entry point"
```

---

## Task 6: Add Integration Test for OAuth Flow

**Files:**
- Create: `tests/test_oauth.py`

**Step 1: Write integration test skeleton**

```python
"""
OAuth integration tests.

These tests verify the OAuth flow works with mocked Cloudflare Access responses.
"""

import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient


@pytest.fixture
def mock_access_config(monkeypatch):
    """Configure Access credentials for testing."""
    monkeypatch.setenv("ACCESS_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ACCESS_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_TEAM_NAME", "test-team")
    monkeypatch.setenv("MCP_SERVER_URL", "http://localhost:8000")


def test_oauth_metadata_endpoint(mock_access_config):
    """Server exposes OAuth discovery metadata."""
    from redlib_mcp import create_authenticated_server

    server = create_authenticated_server()
    app = server.http_app()
    client = TestClient(app)

    response = client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == 200
    data = response.json()
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data


def test_protected_endpoint_requires_auth(mock_access_config):
    """MCP endpoints return 401 without valid token."""
    from redlib_mcp import create_authenticated_server

    server = create_authenticated_server()
    app = server.http_app()
    client = TestClient(app)

    # Try to access MCP endpoint without auth
    response = client.post("/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})

    assert response.status_code == 401


def test_unauthenticated_server_allows_access(monkeypatch):
    """Server without auth allows unauthenticated access."""
    monkeypatch.delenv("ACCESS_CLIENT_ID", raising=False)
    monkeypatch.delenv("ACCESS_CLIENT_SECRET", raising=False)

    from redlib_mcp import create_authenticated_server

    server = create_authenticated_server()
    app = server.http_app()
    client = TestClient(app)

    response = client.post("/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})

    # Should succeed without auth when auth is disabled
    assert response.status_code in [200, 202]
```

**Step 2: Run tests**

Run: `nix develop --command pytest tests/test_oauth.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_oauth.py
git commit -m "test: add OAuth integration tests"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md with OAuth configuration**

Add section after "## Configuration":

```markdown
## OAuth Configuration (Optional)

To enable OAuth authentication via Cloudflare Access:

```bash
# Required
export ACCESS_CLIENT_ID="your-client-id"
export ACCESS_CLIENT_SECRET="your-client-secret"
export ACCESS_TEAM_NAME="your-team"

# Optional
export MCP_SERVER_URL="https://your-server.com"  # For OAuth redirects
export MCP_SERVER_HOST="0.0.0.0"                 # Default: 0.0.0.0
export MCP_SERVER_PORT="8000"                    # Default: 8000

# Run HTTP server with OAuth
redlib-mcp-server
```

Without Access credentials, the server runs without authentication.
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add OAuth configuration to CLAUDE.md"
```

---

## Task 8: Final Verification

**Step 1: Run full test suite**

Run: `nix develop --command pytest tests/ -v`
Expected: All tests pass

**Step 2: Manual smoke test (without real Access)**

Run: `nix develop --command python -c "from redlib_mcp import main_server, create_authenticated_server; print('Import OK')"`
Expected: "Import OK"

**Step 3: Verify stdio transport still works**

Run: `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | nix develop --command redlib-mcp 2>/dev/null | head -1`
Expected: JSON response with tools list

**Step 4: Final commit if any changes**

```bash
git status
# If clean, done. If changes, commit them.
```

---

## Summary

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| 1 | Update dependencies | 5 min |
| 2 | Update imports | 5 min |
| 3 | Add Access config loading | 15 min |
| 4 | Create HTTP server entry point | 20 min |
| 5 | Update entry points | 5 min |
| 6 | Add OAuth tests | 15 min |
| 7 | Update documentation | 5 min |
| 8 | Final verification | 10 min |

Total: ~80 minutes of implementation work.
