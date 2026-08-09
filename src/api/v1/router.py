from fastapi import APIRouter
from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.batch import router as batch_router
from src.api.v1.endpoints.crawl import router as crawl_router
from src.api.v1.endpoints.projects import router as projects_router
from src.api.v1.endpoints.ai import router as ai_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(crawl_router)
api_v1_router.include_router(batch_router)
api_v1_router.include_router(ai_router)
