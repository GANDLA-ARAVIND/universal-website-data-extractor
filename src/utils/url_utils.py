"""URL Normalization and Domain Scope Utilities.

Provides robust URL validation, canonical normalization, absolute link resolution,
and domain scope checking.
"""

import ipaddress
import socket
from typing import List, Tuple
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from src.core.config import settings
from src.core.exceptions import InvalidURLException

BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0", "broadcasthost"}
BLOCKED_TLDS = (".local", ".internal", ".lan", ".home", ".arpa")


def is_private_or_restricted_ip(ip_str: str) -> bool:
    """Checks whether an IP address belongs to a private, loopback, link-local,
    multicast, or reserved subnet. Returns False if ip_str is not a valid IP literal.
    """
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def validate_public_url(url: str) -> str:
    """Validates that a URL is a well-formed public HTTP or HTTPS web address,
    enforcing SSRF protection against loopback, private subnets, and metadata endpoints.

    Args:
        url (str): Input URL string.

    Returns:
        str: Normalized valid URL string.

    Raises:
        InvalidURLException: If URL scheme is invalid, missing hostname, or targets private IP.
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

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        raise InvalidURLException(f"Invalid URL '{url}'. Missing valid hostname.")

    # Perform SSRF Validation if enabled and private IPs are disallowed
    if getattr(settings, "ENABLE_SSRF_PROTECTION", True) and not getattr(settings, "ALLOW_PRIVATE_IPS", False):
        if hostname in BLOCKED_HOSTNAMES or any(hostname.endswith(tld) for tld in BLOCKED_TLDS):
            raise InvalidURLException(
                f"SSRF Protection Error: Target host '{hostname}' is restricted."
            )

        # Check if hostname is an explicit IP literal
        try:
            if is_private_or_restricted_ip(hostname):
                raise InvalidURLException(
                    f"SSRF Protection Error: Target IP address '{hostname}' belongs to a private or restricted subnet."
                )
        except ValueError:
            pass

        # Perform DNS resolution to verify resolved IP addresses
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in addr_info:
                ip_addr = sockaddr[0]
                if is_private_or_restricted_ip(ip_addr):
                    raise InvalidURLException(
                        f"SSRF Protection Error: Target domain '{hostname}' resolves to restricted IP '{ip_addr}'."
                    )
        except socket.gaierror:
            raise InvalidURLException(
                f"Invalid Target Domain '{hostname}': Failed to resolve host via DNS."
            )

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


NON_HTML_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp", ".tiff",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".tar",
    ".gz", ".7z", ".rar", ".exe", ".dmg", ".iso", ".apk", ".mp3", ".mp4",
    ".wav", ".avi", ".mov", ".flv", ".wmv", ".mkv", ".css", ".js", ".json",
    ".xml", ".rss", ".atom", ".woff", ".woff2", ".ttf", ".eot", ".otf"
}


def is_crawlable_html_url(url: str) -> bool:
    """Checks if a URL points to a crawlable HTML page rather than a static asset or binary file.

    Args:
        url (str): Target URL string.

    Returns:
        bool: True if URL is likely an HTML page, False if it is a non-HTML asset.
    """
    if not url or not isinstance(url, str):
        return False

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        return False

    path = parsed.path.lower()
    # Check if path ends with a known non-HTML static asset extension
    for ext in NON_HTML_EXTENSIONS:
        if path.endswith(ext):
            return False

    return True


def is_external_link(base_url: str, target_url: str) -> bool:
    """Determines whether a link points to an external third-party domain.

    Args:
        base_url (str): Parent page URL.
        target_url (str): Discovered hyperlink target URL.

    Returns:
        bool: True if external, False if internal.
    """
    return not is_same_domain(base_url, target_url)


def build_website_structure_tree(urls: List[str], seed_url: str) -> Tuple[List[str], List[str]]:
    """Builds a deterministic hierarchical ASCII tree representation and main navigation sections
    from a list of crawled URLs.

    Args:
        urls (List[str]): List of extracted page URLs.
        seed_url (str): Target seed URL.

    Returns:
        Tuple of (tree_lines: List[str], main_sections: List[str])
    """
    if not urls:
        return [f"Home ({seed_url})"], []

    paths = set()
    for u in urls:
        parsed = urlparse(u)
        path = parsed.path.strip("/")
        if path:
            paths.add(path)

    if not paths:
        return [f"Home ({seed_url})"], []

    sorted_paths = sorted(list(paths))

    main_sections_set = set()
    for p in sorted_paths:
        top_segment = p.split("/")[0]
        if top_segment:
            main_sections_set.add(f"/{top_segment}")
    main_sections = sorted(list(main_sections_set))

    tree_lines = [f"Home ({seed_url})"]
    path_nodes: dict = {}
    for p in sorted_paths:
        parts = p.split("/")
        current = path_nodes
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    def _render_tree(node_dict: dict, prefix: str = "") -> List[str]:
        lines = []
        keys = sorted(node_dict.keys())
        for idx, key in enumerate(keys):
            is_last = (idx == len(keys) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{key}")
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(_render_tree(node_dict[key], child_prefix))
        return lines

    tree_lines.extend(_render_tree(path_nodes))
    return tree_lines, main_sections


