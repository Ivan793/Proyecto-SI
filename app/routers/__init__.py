from fastapi import APIRouter

from .admin import router as admin_router
from . import auth, graduate_router, guest_router, proyect_router, student_router, public_research_router, assistence_router, public_academic_router

router = APIRouter(prefix="/api/v1")

# Agrupar routers principales
router.include_router(admin_router)

router.include_router(auth.router)
router.include_router(graduate_router.router)
router.include_router(guest_router.router)
router.include_router(proyect_router.router)
router.include_router(student_router.router)
router.include_router(public_research_router.router)
router.include_router(assistence_router.router)
router.include_router(public_academic_router.router) 

