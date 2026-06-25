# API v1 Router Package
from fastapi import APIRouter
from app.api.v1.endpoints import router as core_router

api_router = APIRouter()
api_router.include_router(core_router)
