#!/usr/bin/env python3
"""
Redlib MCP Server

MCP server that exposes Redlib's JSON API endpoints to LLMs.
"""

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
