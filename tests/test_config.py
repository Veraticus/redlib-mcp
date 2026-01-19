import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch


class TestLoadConfig:
    def test_env_var_takes_priority(self, tmp_path, monkeypatch):
        from redlib_mcp import load_config

        # Set env var
        monkeypatch.setenv("REDLIB_URL", "http://env.example.com")

        # Create config file with different value
        config_dir = tmp_path / ".config" / "redlib"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"REDLIB_URL": "http://file.example.com"}))

        with patch.object(Path, "home", return_value=tmp_path):
            assert load_config() == "http://env.example.com"

    def test_config_file_used_when_no_env(self, tmp_path, monkeypatch):
        from redlib_mcp import load_config

        monkeypatch.delenv("REDLIB_URL", raising=False)

        config_dir = tmp_path / ".config" / "redlib"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"REDLIB_URL": "http://file.example.com"}))

        with patch.object(Path, "home", return_value=tmp_path):
            assert load_config() == "http://file.example.com"

    def test_default_when_no_config(self, tmp_path, monkeypatch):
        from redlib_mcp import load_config

        monkeypatch.delenv("REDLIB_URL", raising=False)

        with patch.object(Path, "home", return_value=tmp_path):
            assert load_config() == "http://localhost:8080"

    def test_default_when_config_file_missing_key(self, tmp_path, monkeypatch):
        from redlib_mcp import load_config

        monkeypatch.delenv("REDLIB_URL", raising=False)

        config_dir = tmp_path / ".config" / "redlib"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"OTHER_KEY": "value"}))

        with patch.object(Path, "home", return_value=tmp_path):
            assert load_config() == "http://localhost:8080"


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


def test_create_server_with_auth(monkeypatch):
    """Server created with OIDCProxy when Access configured."""
    monkeypatch.setenv("ACCESS_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ACCESS_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("ACCESS_TEAM_NAME", "test-team")
    monkeypatch.setenv("MCP_SERVER_URL", "http://localhost:8000")

    # Mock the OIDC configuration fetch that OIDCProxy does at construction
    mock_oidc_config = {
        "issuer": "https://test-team.cloudflareaccess.com",
        "authorization_endpoint": "https://test-team.cloudflareaccess.com/cdn-cgi/access/sso/oidc/authorize",
        "token_endpoint": "https://test-team.cloudflareaccess.com/cdn-cgi/access/sso/oidc/token",
        "jwks_uri": "https://test-team.cloudflareaccess.com/cdn-cgi/access/certs",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
    }

    with patch("httpx.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.raise_for_status = lambda: None
        mock_response.json.return_value = mock_oidc_config

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
