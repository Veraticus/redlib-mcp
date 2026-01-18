# Redlib MCP Design

An MCP server that exposes Redlib's JSON API endpoints to LLMs.

## Overview

Redlib recently added `.js` endpoints that return JSON instead of HTML. This MCP wraps those endpoints, allowing LLMs to query Reddit content through a privacy-focused proxy.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python | Matches targetprocess-mcp pattern, fast to build |
| Deployment | Same machine as Redlib, configurable URL | Simple, but flexible |
| Tool structure | One tool per endpoint (6 tools) | Direct mapping, predictable, composable |
| URL handling | Accept Reddit or Redlib URLs | User convenience - paste any link |
| Pagination | Expose `after` cursor directly | Transparent, LLM controls fetching |
| Response format | Pass through raw JSON | Low maintenance, no sync burden |
| Error handling | Pass through Redlib errors | Already clean format |

## Project Structure

```
redlib-mcp/
├── src/
│   └── redlib_mcp.py      # Single-file MCP server
├── pyproject.toml          # Dependencies: mcp, httpx
├── flake.nix               # Nix packaging
├── README.md
├── LICENSE
└── CLAUDE.md
```

## Configuration

Priority order:
1. Environment variable: `REDLIB_URL`
2. Config file: `~/.config/redlib/config.json`
3. Default: `http://localhost:8080`

## MCP Tools

### get_subreddit

Fetch posts from a subreddit.

```python
async def get_subreddit(
    subreddit: str,           # "rust" or "r/rust" or reddit URL
    sort: str = "hot",        # hot, new, top, rising
    time: str | None = None,  # hour, day, week, month, year, all (for top)
    after: str | None = None, # pagination cursor
) -> str
```

### get_post

Fetch a post with its comments.

```python
async def get_post(
    post: str,                    # post ID, permalink, or reddit URL
    comment_id: str | None = None, # focus on specific comment thread
) -> str
```

### get_user

Fetch a user's profile and content.

```python
async def get_user(
    username: str,            # "spez" or "u/spez" or reddit URL
    listing: str = "overview", # overview, submitted, comments
    after: str | None = None,
) -> str
```

### search_reddit

Search for posts.

```python
async def search_reddit(
    query: str,
    subreddit: str | None = None,  # limit to specific sub
    after: str | None = None,
) -> str
```

### get_wiki

Fetch a subreddit's wiki page.

```python
async def get_wiki(
    subreddit: str,
    page: str = "index",
) -> str
```

### get_duplicates

Find cross-posts of a post.

```python
async def get_duplicates(
    post: str,  # post ID or URL
) -> str
```

## URL Normalization

All tools accept flexible input formats:

- Full Reddit URLs: `https://reddit.com/r/rust/comments/abc123`
- Old Reddit: `https://old.reddit.com/r/rust`
- www variants: `https://www.reddit.com/r/rust`
- Redlib URLs: `https://redlib.example.com/r/rust`
- Bare paths: `/r/rust`, `r/rust`
- Just names: `rust` (for subreddits), `spez` (for users)

The `normalize_path` function:
1. Strips known domains (reddit.com variants, configured Redlib URL)
2. Ensures path starts with `/`
3. Prepends `/r/` or `/user/` for bare names based on context
4. Strips trailing slashes and query params

## Core Components

### RedlibClient

```python
class RedlibClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def get(self, path: str) -> dict:
        """Fetches {base_url}/{path}.js, returns parsed JSON."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}{path}.js")
            response.raise_for_status()
            return response.json()
```

### Configuration Loading

```python
def load_config() -> str:
    # 1. Environment variable
    if url := os.getenv("REDLIB_URL"):
        return url

    # 2. Config file
    config_path = Path.home() / ".config" / "redlib" / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
        if url := config.get("REDLIB_URL"):
            return url

    # 3. Default
    return "http://localhost:8080"
```

## Dependencies

- `mcp>=1.5.0` - MCP protocol implementation
- `httpx>=0.27.0` - Async HTTP client

## Client Configuration Example

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "redlib": {
      "command": "path/to/redlib-mcp/.venv/bin/python",
      "args": ["-m", "redlib_mcp"],
      "env": {
        "REDLIB_URL": "http://localhost:8080"
      }
    }
  }
}
```
