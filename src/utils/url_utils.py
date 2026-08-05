"""URL Normalization and Domain Scope Utilities.

Provides robust URL validation, canonical normalization, absolute link resolution,
and domain scope checking.
"""

from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from src.core.exceptions import InvalidURLException


def validate_public_url(url: str) -> str:
    """Validates that a URL is a well-formed public HTTP or HTTPS web address.

    Args:
        url (str): Input URL string.

    Returns:
        str: Normalized valid URL string.

    Raises:
        InvalidURLException: If URL scheme is not HTTP/HTTPS or lacks hostname.
    """
    if not url or not isinstance(url, str):
        raise InvalidURLException("URL string must be provided.")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise InvalidURLException(
            f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS protocols are supported."
        )

    if not parsed.netloc:
        raise InvalidURLException(f"Invalid URL '{url}'. Missing valid hostname/domain.")

    return normalize_url(url)


def normalize_url(url: str) -> str:
    """Canonicalizes a URL by converting host to lowercase, stripping fragments,
    sorting query parameters, and stripping trailing slashes.

    Args:
        url (str): Input URL string.

    Returns:
        str: Canonical normalized URL.
    """
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports if present
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path
    if not path:
        path = "/"
    elif len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    # Sort query parameters for canonical consistency
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    sorted_query = urlencode(sorted(query_params))

    # Strip fragment completely
    return urlunparse((scheme, netloc, path, parsed.params, sorted_query, ""))


def resolve_absolute_url(base_url: str, target_url: str) -> str:
    """Resolves relative URL paths against a base page URL into an absolute normalized URL.

    Args:
        base_url (str): Parent page absolute URL.
        target_url (str): Discovered link URL (relative or absolute).

    Returns:
        str: Absolute normalized target URL.
    """
    joined = urljoin(base_url, target_url)
    return normalize_url(joined)


def is_same_domain(seed_url: str, target_url: str) -> bool:
    """Checks if a target URL belongs to the same domain as the seed URL.

    Args:
        seed_url (str): Seed website URL.
        target_url (str): Target page URL.

    Returns:
        bool: True if domains match, False otherwise.
    """
    seed_netloc = urlparse(seed_url).netloc.lower()
    target_netloc = urlparse(target_url).netloc.lower()

    # Normalize www. prefix for domain matching
    seed_domain = seed_netloc[4:] if seed_netloc.startswith("www.") else seed_netloc
    target_domain = target_netloc[4:] if target_netloc.startswith("www.") else target_netloc

    return seed_domain == target_domain


def is_external_link(base_url: str, target_url: str) -> bool:
    """Determines whether a link points to an external third-party domain.

    Args:
        base_url (str): Parent page URL.
        target_url (str): Discovered hyperlink target URL.

    Returns:
        bool: True if external, False if internal.
    """
    return not is_same_domain(base_url, target_url)
