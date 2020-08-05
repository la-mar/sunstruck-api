from fastapi import APIRouter

from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.health import router as health_router
from api.v1.endpoints.users import router as users_router

__all__ = ["api_router"]

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, tags=["Login"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
