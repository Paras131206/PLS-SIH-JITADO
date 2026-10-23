from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, batches

api_router = APIRouter()
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(batches.router, prefix="/batches", tags=["Batches"])