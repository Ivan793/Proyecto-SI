from fastapi import APIRouter

from . import events, group, subject, teacher, teacher_subject

router = APIRouter(prefix="/admin", tags=["Administrador"])

router.include_router(events.router, prefix="/eventos")
router.include_router(teacher.router, prefix="/profesores")
router.include_router(subject.router, prefix="/materias")
router.include_router(group.router, prefix="/grupos")
router.include_router(teacher_subject.router, prefix="/asignaciones-docentes")
