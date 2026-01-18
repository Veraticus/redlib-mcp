#!/usr/bin/env python3
"""
Redlib MCP Server

MCP server that exposes Redlib's JSON API endpoints to LLMs.
"""

import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

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
