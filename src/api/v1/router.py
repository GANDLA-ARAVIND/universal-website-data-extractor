"""API V1 Router Aggregator."""

from fastapi import APIRouter
from src.api.v1.endpoints.crawl import router as crawl_router

api_v1_router = APIRouter()
api_v1_router.include_router(crawl_router)
