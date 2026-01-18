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
