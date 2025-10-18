from fastapi import APIRouter

from .admin import router as admin_router
from . import auth

router = APIRouter(prefix="/api/v1")

# Agrupar routers principales
router.include_router(admin_router)

router.include_router(auth.router)


