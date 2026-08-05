"""Fetcher strategies package for static HTTP and dynamic Playwright fetching."""

from src.crawler.fetchers.base import BaseFetcher, FetchResult
from src.crawler.fetchers.static_fetcher import StaticFetcher
from src.crawler.fetchers.dynamic_fetcher import DynamicFetcher

__all__ = ["BaseFetcher", "FetchResult", "StaticFetcher", "DynamicFetcher"]
