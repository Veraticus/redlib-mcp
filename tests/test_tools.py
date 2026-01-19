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
            "posts": [{"title": "Hello Rust", "id": "123", "author": {"name": "user1"}}],
            "after": "abc123"
        },
        "error": None
    }

    # Expected after stripping - fields outside POST_FIELDS are removed
    expected = {
        "data": {
            "subreddit": {"name": "rust"},
            "posts": [{"title": "Hello Rust", "id": "123", "author": "user1"}],
            "after": "abc123"
        }
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_subreddit.fn("rust")

    assert json.loads(result) == expected


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
            "post": {"id": "abc123", "title": "Test", "author": {"name": "poster"}},
            "comments": []
        },
        "error": None
    }

    # Expected after stripping - author simplified to name string
    expected = {
        "data": {
            "post": {"id": "abc123", "title": "Test", "author": "poster"},
            "comments": []
        }
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_post.fn("abc123")

    assert json.loads(result) == expected


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

    # Expected after stripping - user field not in strip_response, so data wrapper recurses
    expected = {
        "data": {
            "posts": [],
            "after": None
        }
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_user.fn("spez")

    assert json.loads(result) == expected


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
            "posts": [{"title": "Result 1", "id": "r1", "author": {"name": "user1"}}],
            "after": "abc123"
        },
        "error": None
    }

    # Expected after stripping
    expected = {
        "data": {
            "posts": [{"title": "Result 1", "id": "r1", "author": "user1"}],
            "after": "abc123"
        }
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await search_reddit.fn("rust programming")

    assert json.loads(result) == expected


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
            "wiki_page": "index",
            "content": "# Wiki content"
        },
        "error": None
    }

    # Expected after stripping - data wrapper recurses, keeps recognized keys
    expected = {
        "data": {
            "subreddit": "rust",
            "wiki_page": "index",
            "content": "# Wiki content"
        }
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_wiki.fn("rust")

    assert json.loads(result) == expected


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
            "post": {"id": "abc123", "title": "Test", "author": {"name": "poster"}},
            "duplicates": [{"id": "xyz789", "title": "Dup", "author": {"name": "other"}}]
        },
        "error": None
    }

    # Expected after stripping - author simplified
    expected = {
        "data": {
            "post": {"id": "abc123", "title": "Test", "author": "poster"},
            "duplicates": [{"id": "xyz789", "title": "Dup", "author": "other"}]
        }
    }

    with patch("redlib_mcp.client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_duplicates.fn("abc123")

    assert json.loads(result) == expected


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


# Unit tests for strip_response helper functions
class TestStripResponse:
    def test_strip_post_basic(self):
        from redlib_mcp import strip_post

        post = {
            "id": "abc123",
            "title": "Test Post",
            "body": "Content here",
            "author": {"name": "user1", "flair": {"text": "flair"}},
            "score": 100,
            "subreddit": "rust",
            "permalink": "/r/rust/comments/abc123",
            "extra_field": "should be removed",
            "awards": [{"name": "Gold"}],
        }

        result = strip_post(post)

        assert result["id"] == "abc123"
        assert result["title"] == "Test Post"
        assert result["body"] == "Content here"
        assert result["author"] == "user1"  # Simplified to string
        assert result["score"] == 100
        assert "extra_field" not in result
        assert "awards" not in result  # Not in POST_FIELDS

    def test_strip_comment_basic(self):
        from redlib_mcp import strip_comment

        comment = {
            "id": "xyz789",
            "body": "A comment",
            "author": {"name": "commenter", "flair": {"text": "mod"}},
            "score": 50,
            "created": "1234567890",
            "kind": "t1",
            "post_link": "/r/rust/comments/abc123",
            "prefs": {"show_nsfw": True},
            "replies": [],
        }

        result = strip_comment(comment)

        assert result["id"] == "xyz789"
        assert result["body"] == "A comment"
        assert result["author"] == "commenter"  # Simplified
        assert result["score"] == 50
        assert "post_link" not in result
        assert "prefs" not in result
        assert "replies" in result

    def test_strip_comment_nested_replies(self):
        from redlib_mcp import strip_comment

        comment = {
            "id": "parent",
            "body": "Parent",
            "author": {"name": "user1"},
            "score": 10,
            "kind": "t1",
            "replies": [
                {
                    "id": "child",
                    "body": "Child",
                    "author": {"name": "user2"},
                    "score": 5,
                    "kind": "t1",
                    "post_link": "should be removed",
                    "replies": [],
                }
            ],
        }

        result = strip_comment(comment)

        assert result["author"] == "user1"
        assert len(result["replies"]) == 1
        assert result["replies"][0]["author"] == "user2"
        assert "post_link" not in result["replies"][0]

    def test_strip_response_full(self):
        from redlib_mcp import strip_response

        data = {
            "post": {
                "id": "abc123",
                "title": "Test",
                "author": {"name": "poster"},
                "extra": "gone",
            },
            "comments": [
                {
                    "id": "c1",
                    "body": "Hi",
                    "author": {"name": "commenter"},
                    "post_link": "removed",
                    "replies": [],
                }
            ],
            "after": "cursor123",
            "error": None,  # Not preserved
        }

        result = strip_response(data)

        assert result["post"]["id"] == "abc123"
        assert result["post"]["author"] == "poster"
        assert "extra" not in result["post"]
        assert result["comments"][0]["author"] == "commenter"
        assert "post_link" not in result["comments"][0]
        assert result["after"] == "cursor123"
        assert "error" not in result
