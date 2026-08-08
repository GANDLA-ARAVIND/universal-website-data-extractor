"""Unit tests for SSRF Protection and IP Resolution Validation."""

import pytest
from src.core.config import settings
from src.core.exceptions import InvalidURLException
from src.utils.url_utils import is_private_or_restricted_ip, validate_public_url


def test_is_private_or_restricted_ip():
    """Verifies that private, loopback, and metadata IPs are correctly flagged."""
    assert is_private_or_restricted_ip("127.0.0.1") is True
    assert is_private_or_restricted_ip("10.0.0.1") is True
    assert is_private_or_restricted_ip("172.16.0.1") is True
    assert is_private_or_restricted_ip("192.168.1.1") is True
    assert is_private_or_restricted_ip("169.254.169.254") is True
    assert is_private_or_restricted_ip("0.0.0.0") is True
    assert is_private_or_restricted_ip("::1") is True
    assert is_private_or_restricted_ip("93.184.216.34") is False  # Public example.com IP


def test_validate_public_url_valid():
    """Verifies valid public URLs pass validation."""
    valid_url = "https://example.com"
    normalized = validate_public_url(valid_url)
    assert normalized.startswith("https://example.com")


def test_validate_public_url_ssrf_loopback():
    """Verifies loopback and local hostnames are blocked by SSRF protection."""
    with pytest.raises(InvalidURLException, match="restricted|private"):
        validate_public_url("http://127.0.0.1/admin")

    with pytest.raises(InvalidURLException, match="restricted"):
        validate_public_url("http://localhost:8000/docs")

    with pytest.raises(InvalidURLException, match="restricted"):
        validate_public_url("http://0.0.0.0:5000/")


def test_validate_public_url_ssrf_private_subnets():
    """Verifies private IP addresses are rejected."""
    with pytest.raises(InvalidURLException, match="private"):
        validate_public_url("http://10.0.0.1/secret")

    with pytest.raises(InvalidURLException, match="private"):
        validate_public_url("http://192.168.1.100/config")

    with pytest.raises(InvalidURLException, match="private"):
        validate_public_url("http://169.254.169.254/latest/meta-data/")


def test_validate_public_url_ssrf_restricted_tld():
    """Verifies internal local TLDs are rejected."""
    with pytest.raises(InvalidURLException, match="restricted"):
        validate_public_url("http://service.internal/api")

    with pytest.raises(InvalidURLException, match="restricted"):
        validate_public_url("http://dashboard.local/")
