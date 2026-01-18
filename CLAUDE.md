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
