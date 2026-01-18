# Redlib MCP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MCP server that exposes Redlib's JSON API endpoints to LLMs.

**Architecture:** Single-file Python MCP server using FastMCP. RedlibClient wraps httpx for API calls. URL normalization accepts Reddit/Redlib URLs and converts to paths. Six tools map 1:1 to Redlib endpoints.

**Tech Stack:** Python 3.12, FastMCP, httpx, pytest, Nix flakes

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `flake.nix`
- Create: `LICENSE`
- Create: `CLAUDE.md`
- Create: `src/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "redlib-mcp"
version = "0.1.0"
description = "MCP server for Redlib - privacy-focused Reddit frontend"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.5.0",
    "httpx>=0.27.0",
]

[project.scripts]
redlib-mcp = "redlib_mcp:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

**Step 2: Create flake.nix**

```nix
{
  description = "Redlib MCP Server - Model Context Protocol server for Redlib API";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;

        redlib-mcp = pythonPackages.buildPythonApplication rec {
          pname = "redlib-mcp";
          version = "0.1.0";
          src = ./.;
          pyproject = true;

          nativeBuildInputs = with pythonPackages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pythonPackages; [
            mcp
            httpx
          ];

          pythonImportsCheck = [ "redlib_mcp" ];

          meta = with pkgs.lib; {
            description = "Model Context Protocol server for Redlib API";
            license = licenses.mit;
            platforms = platforms.unix;
          };
        };

      in
      {
        packages = {
          inherit redlib-mcp;
          default = redlib-mcp;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            pythonPackages.pip
            pythonPackages.black
            pythonPackages.pytest
            pythonPackages.pytest-asyncio
            pythonPackages.mcp
            pythonPackages.httpx
            git
          ];

          shellHook = ''
            echo "Redlib MCP development environment"
            echo "  python src/redlib_mcp.py  - Run the MCP server"
            echo "  pytest                    - Run tests"
            echo "  nix build                 - Build with Nix"
          '';
        };

        apps.default = {
          type = "app";
          program = "${redlib-mcp}/bin/redlib-mcp";
        };
      }
    );
}
```

**Step 3: Create LICENSE (MIT)**

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 4: Create CLAUDE.md**

```markdown
# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Redlib MCP is a Model Context Protocol server that exposes Redlib's JSON API endpoints to LLMs. Redlib is a privacy-focused Reddit frontend, and this MCP allows querying Reddit content through it.

## Development Commands

```bash
# Enter dev shell (Nix)
nix develop

# Run the server
python src/redlib_mcp.py

# Run tests
pytest

# Format code
black src/ tests/
```

## Architecture

Single-file MCP server (`src/redlib_mcp.py`) containing:

1. **RedlibClient** - HTTP client wrapper for Redlib's `.js` endpoints
2. **URL normalization** - Converts Reddit/Redlib URLs to paths
3. **Config loading** - Environment vars → config file → defaults
4. **6 MCP tools** - One per Redlib endpoint (subreddit, post, user, search, wiki, duplicates)

## Configuration

Priority order:
1. `REDLIB_URL` environment variable
2. `~/.config/redlib/config.json` file
3. Default: `http://localhost:8080`

## Adding New Tools

1. Add `@server.tool()` decorated async function
2. Use `normalize_path()` for URL inputs
3. Call `client.get(path)` to fetch data
4. Return `json.dumps(result)`

## Testing

Tests use pytest-asyncio. Mock httpx responses for unit tests.
```

**Step 5: Create src/__init__.py**

```python
# Empty file to make src a package
```

**Step 6: Commit**

```bash
git add pyproject.toml flake.nix LICENSE CLAUDE.md src/__init__.py
git commit -m "feat: add project scaffolding"
```

---

## Task 2: URL Normalization

**Files:**
- Create: `src/redlib_mcp.py` (partial - just normalization)
- Create: `tests/__init__.py`
- Create: `tests/test_normalize.py`

**Step 1: Write the failing tests**

Create `tests/__init__.py` (empty) and `tests/test_normalize.py`:

```python
import pytest
from redlib_mcp import normalize_path, normalize_subreddit, normalize_user, normalize_post


class TestNormalizePath:
    def test_bare_path_with_slash(self):
        assert normalize_path("/r/rust") == "/r/rust"

    def test_bare_path_without_slash(self):
        assert normalize_path("r/rust") == "/r/rust"

    def test_reddit_url(self):
        assert normalize_path("https://reddit.com/r/rust") == "/r/rust"

    def test_old_reddit_url(self):
        assert normalize_path("https://old.reddit.com/r/rust") == "/r/rust"

    def test_www_reddit_url(self):
        assert normalize_path("https://www.reddit.com/r/rust") == "/r/rust"

    def test_np_reddit_url(self):
        assert normalize_path("https://np.reddit.com/r/rust") == "/r/rust"

    def test_strips_trailing_slash(self):
        assert normalize_path("/r/rust/") == "/r/rust"

    def test_strips_query_params(self):
        assert normalize_path("/r/rust?sort=new") == "/r/rust"

    def test_preserves_full_path(self):
        assert normalize_path("https://reddit.com/r/rust/comments/abc123/title") == "/r/rust/comments/abc123/title"

    def test_custom_redlib_url(self):
        assert normalize_path("https://redlib.example.com/r/rust", redlib_url="https://redlib.example.com") == "/r/rust"


class TestNormalizeSubreddit:
    def test_bare_name(self):
        assert normalize_subreddit("rust") == "/r/rust"

    def test_with_r_prefix(self):
        assert normalize_subreddit("r/rust") == "/r/rust"

    def test_with_slash_r_prefix(self):
        assert normalize_subreddit("/r/rust") == "/r/rust"

    def test_full_url(self):
        assert normalize_subreddit("https://reddit.com/r/rust") == "/r/rust"


class TestNormalizeUser:
    def test_bare_name(self):
        assert normalize_user("spez") == "/user/spez"

    def test_with_u_prefix(self):
        assert normalize_user("u/spez") == "/user/spez"

    def test_with_user_prefix(self):
        assert normalize_user("user/spez") == "/user/spez"

    def test_full_url(self):
        assert normalize_user("https://reddit.com/user/spez") == "/user/spez"


class TestNormalizePost:
    def test_just_id(self):
        assert normalize_post("abc123") == "/comments/abc123"

    def test_full_path(self):
        assert normalize_post("/r/rust/comments/abc123/title") == "/r/rust/comments/abc123/title"

    def test_full_url(self):
        assert normalize_post("https://reddit.com/r/rust/comments/abc123/some_title") == "/r/rust/comments/abc123/some_title"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_normalize.py -v`
Expected: FAIL with import errors

**Step 3: Write the implementation**

Create `src/redlib_mcp.py`:

```python
#!/usr/bin/env python3
"""
Redlib MCP Server

MCP server that exposes Redlib's JSON API endpoints to LLMs.
"""

import re
from urllib.parse import urlparse

# Known Reddit domains to strip
REDDIT_DOMAINS = {
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
    "np.reddit.com",
    "i.reddit.com",
    "m.reddit.com",
}


def normalize_path(url: str, redlib_url: str | None = None) -> str:
    """
    Normalize a Reddit/Redlib URL or path to a clean path.

    Accepts:
    - Full Reddit URLs: https://reddit.com/r/rust
    - Redlib URLs: https://redlib.example.com/r/rust
    - Bare paths: /r/rust, r/rust

    Returns: /r/rust (clean path)
    """
    # Parse URL if it looks like one
    if url.startswith("http://") or url.startswith("https://"):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Strip known Reddit domains
        if domain in REDDIT_DOMAINS:
            url = parsed.path
        # Strip configured Redlib domain
        elif redlib_url:
            redlib_parsed = urlparse(redlib_url)
            if domain == redlib_parsed.netloc.lower():
                url = parsed.path
        else:
            url = parsed.path

    # Strip query params
    if "?" in url:
        url = url.split("?")[0]

    # Ensure leading slash
    if not url.startswith("/"):
        url = "/" + url

    # Strip trailing slash
    url = url.rstrip("/")

    return url


def normalize_subreddit(subreddit: str, redlib_url: str | None = None) -> str:
    """
    Normalize a subreddit input to a path.

    Accepts: "rust", "r/rust", "/r/rust", "https://reddit.com/r/rust"
    Returns: "/r/rust"
    """
    path = normalize_path(subreddit, redlib_url)

    # If it's just a name (no slashes after normalization cleanup), add /r/
    if not path.startswith("/r/") and not path.startswith("/user/"):
        # Remove leading slash for check
        name = path.lstrip("/")
        if "/" not in name:
            return f"/r/{name}"

    return path


def normalize_user(username: str, redlib_url: str | None = None) -> str:
    """
    Normalize a username input to a path.

    Accepts: "spez", "u/spez", "user/spez", "https://reddit.com/user/spez"
    Returns: "/user/spez"
    """
    path = normalize_path(username, redlib_url)

    # Handle u/ prefix (convert to user/)
    if path.startswith("/u/"):
        path = "/user/" + path[3:]

    # If it's just a name, add /user/
    if not path.startswith("/user/") and not path.startswith("/r/"):
        name = path.lstrip("/")
        if "/" not in name:
            return f"/user/{name}"

    return path


def normalize_post(post: str, redlib_url: str | None = None) -> str:
    """
    Normalize a post input to a path.

    Accepts: "abc123", "/r/rust/comments/abc123/title", full URL
    Returns: "/comments/abc123" or "/r/rust/comments/abc123/title"
    """
    path = normalize_path(post, redlib_url)

    # If it's just an ID (no slashes), make it a comments path
    name = path.lstrip("/")
    if "/" not in name and not name.startswith("comments"):
        return f"/comments/{name}"

    return path
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_normalize.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/__init__.py tests/test_normalize.py
git commit -m "feat: add URL normalization functions"
```

---

## Task 3: Configuration Loading

**Files:**
- Modify: `src/redlib_mcp.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing tests**

Create `tests/test_config.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with "cannot import name 'load_config'"

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
import json
import os
from pathlib import Path


def load_config() -> str:
    """
    Load Redlib URL from configuration.

    Priority:
    1. REDLIB_URL environment variable
    2. ~/.config/redlib/config.json
    3. Default: http://localhost:8080
    """
    # 1. Environment variable
    if url := os.getenv("REDLIB_URL"):
        return url

    # 2. Config file
    config_path = Path.home() / ".config" / "redlib" / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            if url := config.get("REDLIB_URL"):
                return url
        except (json.JSONDecodeError, IOError):
            pass

    # 3. Default
    return "http://localhost:8080"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_config.py
git commit -m "feat: add configuration loading"
```

---

## Task 4: RedlibClient

**Files:**
- Modify: `src/redlib_mcp.py`
- Create: `tests/test_client.py`

**Step 1: Write the failing tests**

Create `tests/test_client.py`:

```python
import pytest
import httpx
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_client_get_success():
    from redlib_mcp import RedlibClient

    client = RedlibClient("http://localhost:8080")

    mock_response = httpx.Response(
        200,
        json={"data": {"posts": []}, "error": None}
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        result = await client.get("/r/rust")

    assert result == {"data": {"posts": []}, "error": None}


@pytest.mark.asyncio
async def test_client_appends_js_extension():
    from redlib_mcp import RedlibClient

    client = RedlibClient("http://localhost:8080")

    mock_response = httpx.Response(200, json={"data": None, "error": None})
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

    mock_response = httpx.Response(200, json={"data": None, "error": None})
    mock_get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.get", mock_get):
        await client.get("/r/rust")

    call_url = mock_get.call_args[0][0]
    assert call_url == "http://localhost:8080/r/rust.js"


@pytest.mark.asyncio
async def test_client_passes_query_params():
    from redlib_mcp import RedlibClient

    client = RedlibClient("http://localhost:8080")

    mock_response = httpx.Response(200, json={"data": None, "error": None})
    mock_get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.get", mock_get):
        await client.get("/r/rust", params={"sort": "new", "after": "abc123"})

    call_kwargs = mock_get.call_args[1]
    assert call_kwargs["params"] == {"sort": "new", "after": "abc123"}
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_client.py -v`
Expected: FAIL with "cannot import name 'RedlibClient'"

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
import httpx


class RedlibClient:
    """HTTP client for Redlib's JSON API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def get(self, path: str, params: dict | None = None) -> dict:
        """
        Fetch JSON from a Redlib endpoint.

        Appends .js to the path to get JSON response.
        """
        url = f"{self.base_url}{path}.js"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_client.py
git commit -m "feat: add RedlibClient HTTP wrapper"
```

---

## Task 5: MCP Server Setup and get_subreddit Tool

**Files:**
- Modify: `src/redlib_mcp.py`
- Create: `tests/test_tools.py`

**Step 1: Write the failing tests**

Create `tests/test_tools.py`:

```python
import json
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_subreddit_basic():
    from redlib_mcp import get_subreddit

    mock_data = {
        "data": {
            "subreddit": {"name": "rust"},
            "posts": [{"title": "Hello Rust"}],
            "after": "abc123"
        },
        "error": None
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_subreddit("rust")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_subreddit_with_sort():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit("rust", sort="new")

        # Check the path includes sort
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/new"


@pytest.mark.asyncio
async def test_get_subreddit_with_time_filter():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit("rust", sort="top", time="week")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["t"] == "week"


@pytest.mark.asyncio
async def test_get_subreddit_with_pagination():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit("rust", after="cursor123")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["after"] == "cursor123"


@pytest.mark.asyncio
async def test_get_subreddit_accepts_reddit_url():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit("https://reddit.com/r/rust")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/hot"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py::test_get_subreddit_basic -v`
Expected: FAIL

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = FastMCP("redlib-mcp")

# Global client instance
client: RedlibClient | None = None


def init_client():
    """Initialize the Redlib client from configuration."""
    global client
    base_url = load_config()
    client = RedlibClient(base_url)
    logger.info(f"Initialized Redlib client for {base_url}")


@server.tool()
async def get_subreddit(
    subreddit: str,
    sort: str = "hot",
    time: str | None = None,
    after: str | None = None,
) -> str:
    """
    Fetch posts from a subreddit.

    Args:
        subreddit: Subreddit name, r/name, or Reddit URL
        sort: Sort order - hot, new, top, rising
        time: Time filter for top sort - hour, day, week, month, year, all
        after: Pagination cursor from previous response

    Returns:
        JSON with subreddit info, posts array, and pagination cursor
    """
    if client is None:
        init_client()

    path = normalize_subreddit(subreddit)

    # Append sort to path
    if sort and sort != "hot":
        path = f"{path}/{sort}"
    else:
        path = f"{path}/hot"

    # Build query params
    params = {}
    if time:
        params["t"] = time
    if after:
        params["after"] = after

    result = await client.get(path, params=params if params else None)
    return json.dumps(result)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_tools.py
git commit -m "feat: add MCP server setup and get_subreddit tool"
```

---

## Task 6: get_post Tool

**Files:**
- Modify: `src/redlib_mcp.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing tests**

Add to `tests/test_tools.py`:

```python
@pytest.mark.asyncio
async def test_get_post_by_id():
    from redlib_mcp import get_post

    mock_data = {
        "data": {
            "post": {"id": "abc123", "title": "Test"},
            "comments": []
        },
        "error": None
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_post("abc123")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_post_by_url():
    from redlib_mcp import get_post

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_post("https://reddit.com/r/rust/comments/abc123/some_title")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/comments/abc123/some_title"


@pytest.mark.asyncio
async def test_get_post_with_comment_focus():
    from redlib_mcp import get_post

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_post("abc123", comment_id="xyz789")

        call_args = mock_client.get.call_args
        assert "/xyz789" in call_args[0][0]
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py::test_get_post_by_id -v`
Expected: FAIL

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
@server.tool()
async def get_post(
    post: str,
    comment_id: str | None = None,
) -> str:
    """
    Fetch a post with its comments.

    Args:
        post: Post ID, permalink path, or Reddit URL
        comment_id: Optional comment ID to focus on a specific thread

    Returns:
        JSON with post data and comments array
    """
    if client is None:
        init_client()

    path = normalize_post(post)

    # Append comment ID if focusing on specific thread
    if comment_id:
        # Ensure comment_id doesn't have leading slash
        comment_id = comment_id.lstrip("/")
        path = f"{path}/{comment_id}"

    result = await client.get(path)
    return json.dumps(result)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v -k "get_post"`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_tools.py
git commit -m "feat: add get_post tool"
```

---

## Task 7: get_user Tool

**Files:**
- Modify: `src/redlib_mcp.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing tests**

Add to `tests/test_tools.py`:

```python
@pytest.mark.asyncio
async def test_get_user_basic():
    from redlib_mcp import get_user

    mock_data = {
        "data": {
            "user": {"name": "spez"},
            "posts": [],
            "after": None
        },
        "error": None
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_user("spez")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_user_with_listing():
    from redlib_mcp import get_user

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_user("spez", listing="submitted")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/user/spez/submitted"


@pytest.mark.asyncio
async def test_get_user_with_pagination():
    from redlib_mcp import get_user

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_user("spez", after="cursor123")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["after"] == "cursor123"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py::test_get_user_basic -v`
Expected: FAIL

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
@server.tool()
async def get_user(
    username: str,
    listing: str = "overview",
    after: str | None = None,
) -> str:
    """
    Fetch a user's profile and content.

    Args:
        username: Username, u/name, or Reddit user URL
        listing: Content type - overview, submitted, comments
        after: Pagination cursor from previous response

    Returns:
        JSON with user info, posts array, and pagination cursor
    """
    if client is None:
        init_client()

    path = normalize_user(username)

    # Append listing type
    if listing and listing != "overview":
        path = f"{path}/{listing}"

    # Build query params
    params = {}
    if after:
        params["after"] = after

    result = await client.get(path, params=params if params else None)
    return json.dumps(result)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v -k "get_user"`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_tools.py
git commit -m "feat: add get_user tool"
```

---

## Task 8: search_reddit Tool

**Files:**
- Modify: `src/redlib_mcp.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing tests**

Add to `tests/test_tools.py`:

```python
@pytest.mark.asyncio
async def test_search_reddit_basic():
    from redlib_mcp import search_reddit

    mock_data = {
        "data": {
            "posts": [{"title": "Result 1"}],
            "after": "abc123"
        },
        "error": None
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await search_reddit("rust programming")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_search_reddit_with_subreddit():
    from redlib_mcp import search_reddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await search_reddit("async", subreddit="rust")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/search"


@pytest.mark.asyncio
async def test_search_reddit_query_param():
    from redlib_mcp import search_reddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await search_reddit("rust programming")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["q"] == "rust programming"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py::test_search_reddit_basic -v`
Expected: FAIL

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
@server.tool()
async def search_reddit(
    query: str,
    subreddit: str | None = None,
    after: str | None = None,
) -> str:
    """
    Search for posts on Reddit.

    Args:
        query: Search query string
        subreddit: Optional subreddit to limit search to
        after: Pagination cursor from previous response

    Returns:
        JSON with search results and pagination cursor
    """
    if client is None:
        init_client()

    if subreddit:
        sub_path = normalize_subreddit(subreddit)
        path = f"{sub_path}/search"
    else:
        path = "/search"

    params = {"q": query}
    if after:
        params["after"] = after

    result = await client.get(path, params=params)
    return json.dumps(result)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v -k "search"`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_tools.py
git commit -m "feat: add search_reddit tool"
```

---

## Task 9: get_wiki Tool

**Files:**
- Modify: `src/redlib_mcp.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing tests**

Add to `tests/test_tools.py`:

```python
@pytest.mark.asyncio
async def test_get_wiki_index():
    from redlib_mcp import get_wiki

    mock_data = {
        "data": {
            "subreddit": "rust",
            "page": "index",
            "content": "# Wiki content"
        },
        "error": None
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_wiki("rust")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_wiki_specific_page():
    from redlib_mcp import get_wiki

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_wiki("rust", page="faq")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/wiki/faq"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py::test_get_wiki_index -v`
Expected: FAIL

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
@server.tool()
async def get_wiki(
    subreddit: str,
    page: str = "index",
) -> str:
    """
    Fetch a subreddit's wiki page.

    Args:
        subreddit: Subreddit name, r/name, or Reddit URL
        page: Wiki page name (default: index)

    Returns:
        JSON with subreddit, page name, and content
    """
    if client is None:
        init_client()

    sub_path = normalize_subreddit(subreddit)
    path = f"{sub_path}/wiki/{page}"

    result = await client.get(path)
    return json.dumps(result)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v -k "wiki"`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_tools.py
git commit -m "feat: add get_wiki tool"
```

---

## Task 10: get_duplicates Tool

**Files:**
- Modify: `src/redlib_mcp.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing tests**

Add to `tests/test_tools.py`:

```python
@pytest.mark.asyncio
async def test_get_duplicates_by_id():
    from redlib_mcp import get_duplicates

    mock_data = {
        "data": {
            "post": {"id": "abc123"},
            "duplicates": [{"id": "xyz789"}]
        },
        "error": None
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_duplicates("abc123")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_duplicates_by_url():
    from redlib_mcp import get_duplicates

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_duplicates("https://reddit.com/r/rust/comments/abc123/title")

        call_args = mock_client.get.call_args
        # Should convert comments path to duplicates path
        assert "/duplicates/" in call_args[0][0]
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py::test_get_duplicates_by_id -v`
Expected: FAIL

**Step 3: Add the implementation**

Add to `src/redlib_mcp.py`:

```python
@server.tool()
async def get_duplicates(
    post: str,
) -> str:
    """
    Find cross-posts/duplicates of a post.

    Args:
        post: Post ID, permalink, or Reddit URL

    Returns:
        JSON with original post and duplicates array
    """
    if client is None:
        init_client()

    path = normalize_post(post)

    # Convert /comments/ path to /duplicates/ path
    # /r/rust/comments/abc123/title -> /r/rust/duplicates/abc123/title
    # /comments/abc123 -> /duplicates/abc123
    path = path.replace("/comments/", "/duplicates/")

    result = await client.get(path)
    return json.dumps(result)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v -k "duplicates"`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/redlib_mcp.py tests/test_tools.py
git commit -m "feat: add get_duplicates tool"
```

---

## Task 11: Main Entry Point

**Files:**
- Modify: `src/redlib_mcp.py`

**Step 1: Add main function**

Add to the end of `src/redlib_mcp.py`:

```python
def main():
    """Main entry point for the MCP server."""
    init_client()
    server.run()


if __name__ == "__main__":
    main()
```

**Step 2: Test manually**

Run: `python src/redlib_mcp.py`
Expected: Server starts without errors (will wait for MCP connections)

**Step 3: Commit**

```bash
git add src/redlib_mcp.py
git commit -m "feat: add main entry point"
```

---

## Task 12: Final Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
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
```

**Step 2: Run all tests**

Run: `pytest -v`
Expected: All unit tests pass, integration tests skip (unless Redlib running)

**Step 3: Final commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add integration tests"
```

---

## Task 13: Run Full Test Suite and Verify

**Step 1: Run all tests**

```bash
pytest -v
```

Expected: All tests pass

**Step 2: Test nix build**

```bash
nix build
```

Expected: Build succeeds

**Step 3: Final verification commit**

```bash
git add -A
git commit -m "chore: complete redlib-mcp implementation" --allow-empty
```

---

Plan complete and saved to `docs/plans/2026-01-18-redlib-mcp-implementation.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
