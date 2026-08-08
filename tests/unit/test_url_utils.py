"""Unit tests for URL Utilities."""

import pytest
from src.core.exceptions import InvalidURLException
from src.utils.url_utils import (
    is_crawlable_html_url,
    is_external_link,
    is_same_domain,
    normalize_url,
    resolve_absolute_url,
    validate_public_url,
)


def test_validate_public_url_valid() -> None:
    """Verifies that valid HTTP and HTTPS URLs pass validation."""
    url = "https://news.ycombinator.com"
    validated = validate_public_url(url)
    assert validated.startswith("https://news.ycombinator.com")


def test_validate_public_url_invalid_scheme() -> None:
    """Verifies that non-HTTP schemes raise InvalidURLException."""
    with pytest.raises(InvalidURLException):
        validate_public_url("ftp://files.example.com")

    with pytest.raises(InvalidURLException):
        validate_public_url("javascript:alert(1)")


def test_normalize_url_canonicalization() -> None:
    """Verifies URL fragment stripping, host lowercase, and query sorting."""
    raw_url = "HTTP://EXAMPLE.COM:80/about/?b=2&a=1#section1"
    normalized = normalize_url(raw_url)
    assert normalized == "http://example.com/about?a=1&b=2"


def test_is_same_domain() -> None:
    """Verifies same domain matching including www normalization."""
    seed = "https://example.com"
    assert is_same_domain(seed, "https://www.example.com/about") is True
    assert is_same_domain(seed, "https://sub.example.com/contact") is False
    assert is_same_domain(seed, "https://google.com") is False


def test_resolve_absolute_url() -> None:
    """Verifies relative URL resolution against base page URL."""
    base = "https://example.com/blog/article-1"
    resolved = resolve_absolute_url(base, "../about")
    assert resolved == "https://example.com/about"


def test_is_external_link() -> None:
    """Verifies internal vs external link classification."""
    base = "https://example.com"
    assert is_external_link(base, "https://example.com/page2") is False
    assert is_external_link(base, "https://github.com") is True


def test_is_crawlable_html_url() -> None:
    """Verifies HTML page vs non-HTML static asset URL identification."""
    assert is_crawlable_html_url("https://example.com/about") is True
    assert is_crawlable_html_url("https://example.com/page.html") is True
    assert is_crawlable_html_url("https://example.com/document.pdf") is False
    assert is_crawlable_html_url("https://example.com/image.png") is False
    assert is_crawlable_html_url("https://example.com/archive.zip") is False
    assert is_crawlable_html_url("ftp://example.com/file.txt") is False

