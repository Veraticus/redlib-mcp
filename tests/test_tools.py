import json
import pytest
from unittest.mock import AsyncMock, patch


# Note: FastMCP wraps tools in FunctionTool objects.
# Use .fn to access the underlying async function for testing.


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
        result = await get_subreddit.fn("rust")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_subreddit_with_sort():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit.fn("rust", sort="new")

        # Check the path includes sort
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/new"


@pytest.mark.asyncio
async def test_get_subreddit_with_time_filter():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit.fn("rust", sort="top", time="week")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["t"] == "week"


@pytest.mark.asyncio
async def test_get_subreddit_with_pagination():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit.fn("rust", after="cursor123")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["after"] == "cursor123"


@pytest.mark.asyncio
async def test_get_subreddit_accepts_reddit_url():
    from redlib_mcp import get_subreddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_subreddit.fn("https://reddit.com/r/rust")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/hot"


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
        result = await get_post.fn("abc123")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_post_by_url():
    from redlib_mcp import get_post

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_post.fn("https://reddit.com/r/rust/comments/abc123/some_title")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/comments/abc123/some_title"


@pytest.mark.asyncio
async def test_get_post_with_comment_focus():
    from redlib_mcp import get_post

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_post.fn("abc123", comment_id="xyz789")

        call_args = mock_client.get.call_args
        assert "/xyz789" in call_args[0][0]


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
        result = await get_user.fn("spez")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_user_with_listing():
    from redlib_mcp import get_user

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_user.fn("spez", listing="submitted")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/user/spez/submitted"


@pytest.mark.asyncio
async def test_get_user_with_pagination():
    from redlib_mcp import get_user

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_user.fn("spez", after="cursor123")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["after"] == "cursor123"


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
        result = await search_reddit.fn("rust programming")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_search_reddit_with_subreddit():
    from redlib_mcp import search_reddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await search_reddit.fn("async", subreddit="rust")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/search"


@pytest.mark.asyncio
async def test_search_reddit_query_param():
    from redlib_mcp import search_reddit

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await search_reddit.fn("rust programming")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["q"] == "rust programming"


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
        result = await get_wiki.fn("rust")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_wiki_specific_page():
    from redlib_mcp import get_wiki

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_wiki.fn("rust", page="faq")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/r/rust/wiki/faq"


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
        result = await get_duplicates.fn("abc123")

    assert json.loads(result) == mock_data


@pytest.mark.asyncio
async def test_get_duplicates_by_url():
    from redlib_mcp import get_duplicates

    mock_data = {"data": None, "error": None}

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        await get_duplicates.fn("https://reddit.com/r/rust/comments/abc123/title")

        call_args = mock_client.get.call_args
        # Should convert comments path to duplicates path
        assert "/duplicates/" in call_args[0][0]
