"""Crawl Result Extraction Status Classifier.

Analyzes extracted page content, HTTP status codes, titles, headings, and error logs
to classify crawl results into fine-grained outcome statuses (SUCCESS, ANTI_BOT_PROTECTION,
CAPTCHA_DETECTED, LOGIN_REQUIRED, JAVASCRIPT_REQUIRED, ACCESS_DENIED, etc.).
"""

from enum import Enum
from typing import Any, List, Optional


class ExtractionStatus(str, Enum):
    """Fine-grained classification of crawl extraction outcomes."""

    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    NO_CONTENT = "NO_CONTENT"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    ANTI_BOT_PROTECTION = "ANTI_BOT_PROTECTION"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    JAVASCRIPT_REQUIRED = "JAVASCRIPT_REQUIRED"
    ACCESS_DENIED = "ACCESS_DENIED"
    REDIRECT_LOOP = "REDIRECT_LOOP"
    NETWORK_ERROR = "NETWORK_ERROR"


CAPTCHA_KEYWORDS = [
    "captcha",
    "g-recaptcha",
    "hcaptcha",
    "turnstile",
    "verify you are human",
    "verify that you are human",
    "robot check",
    "are you a human",
    "security check to continue",
]

ANTI_BOT_KEYWORDS = [
    "just a moment...",
    "checking your browser",
    "ddos-guard",
    "imperva",
    "incapsula",
    "akamai",
    "cloudflare",
    "attention required! | cloudflare",
    "bot detection",
    "security check",
    "access denied - cloudflare",
]

LOGIN_KEYWORDS = [
    "login required",
    "please log in",
    "please sign in",
    "sign in to continue",
    "log in to continue",
    "authentication required",
    "user login",
]

JS_REQUIRED_KEYWORDS = [
    "enable javascript",
    "you need to enable javascript",
    "javascript is required",
    "requires javascript",
    "please turn on javascript",
]

ACCESS_DENIED_KEYWORDS = [
    "403 forbidden",
    "access denied",
    "access to this page is denied",
    "401 unauthorized",
    "permission denied",
]


def classify_extraction_status(
    pages: List[Any],
    job: Any,
    errors: Optional[List[str]] = None,
) -> ExtractionStatus:
    """Classifies a crawl job's result into a specific ExtractionStatus.

    Args:
        pages (List[Any]): List of extracted page ORM or DTO entities.
        job (Any): CrawlJob ORM model or virtual job instance.
        errors (Optional[List[str]]): List of recorded execution errors.

    Returns:
        ExtractionStatus: The classified extraction outcome.
    """
    job_status_str = (
        job.status.value if hasattr(getattr(job, "status", ""), "value") else str(getattr(job, "status", ""))
    ).upper()

    err_text = " ".join([str(e).lower() for e in (errors or [])])

    # 1. Job level failures without extracted pages
    if not pages or len(pages) == 0 or job_status_str == "FAILED":
        if "redirect" in err_text or "301" in err_text or "302" in err_text or "307" in err_text:
            return ExtractionStatus.REDIRECT_LOOP
        if "403" in err_text or "forbidden" in err_text or "access denied" in err_text:
            return ExtractionStatus.ACCESS_DENIED
        if "timeout" in err_text or "connection" in err_text or "refused" in err_text or "dns" in err_text:
            return ExtractionStatus.NETWORK_ERROR
        if not pages or len(pages) == 0:
            return ExtractionStatus.NO_CONTENT
        return ExtractionStatus.NETWORK_ERROR

    # 2. Inspect primary page
    primary_page = pages[0]
    title = str(getattr(primary_page, "title", "") or "").lower()

    headings_map = getattr(primary_page, "headings", {}) or {}
    all_headings_text = " ".join(
        [h.lower() for h_list in headings_map.values() for h in h_list]
    )
    paragraphs = getattr(primary_page, "paragraphs", []) or []
    all_para_text = " ".join([p.lower() for p in paragraphs[:10]])

    combined_text = f"{title} {all_headings_text} {all_para_text}"

    # Check Captcha
    for kw in CAPTCHA_KEYWORDS:
        if kw in combined_text:
            return ExtractionStatus.CAPTCHA_DETECTED

    # Check Anti-bot Protection
    for kw in ANTI_BOT_KEYWORDS:
        if kw in combined_text:
            return ExtractionStatus.ANTI_BOT_PROTECTION

    # Check JavaScript Required
    for kw in JS_REQUIRED_KEYWORDS:
        if kw in combined_text:
            return ExtractionStatus.JAVASCRIPT_REQUIRED

    # Check Access Denied
    if getattr(primary_page, "status_code", 200) in (403, 401):
        return ExtractionStatus.ACCESS_DENIED
    for kw in ACCESS_DENIED_KEYWORDS:
        if kw in combined_text:
            return ExtractionStatus.ACCESS_DENIED

    # Check Login Required
    for kw in LOGIN_KEYWORDS:
        if kw in combined_text:
            return ExtractionStatus.LOGIN_REQUIRED

    # Check Redirect Loop
    if getattr(primary_page, "status_code", 200) in (301, 302, 307, 308) or "redirect" in err_text:
        return ExtractionStatus.REDIRECT_LOOP

    # Check No Content
    total_paras = sum(len(getattr(p, "paragraphs", []) or []) for p in pages)
    total_headings = sum(
        sum(len(h_list) for h_list in (getattr(p, "headings", {}) or {}).values())
        for p in pages
    )
    if total_paras == 0 and total_headings == 0:
        return ExtractionStatus.NO_CONTENT

    # Check Partial Success
    non_200_cnt = sum(1 for p in pages if getattr(p, "status_code", 200) != 200)
    if non_200_cnt > 0 or (errors and len(errors) > 0):
        return ExtractionStatus.PARTIAL_SUCCESS

    return ExtractionStatus.SUCCESS
