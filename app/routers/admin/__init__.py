from fastapi import APIRouter

from . import events, group, subject, teacher, teacher_subject, student, research

router = APIRouter(prefix="/admin")

router.include_router(events.router, prefix="/eventos")
router.include_router(teacher.router, prefix="/profesores")
router.include_router(subject.router, prefix="/materias")
router.include_router(group.router, prefix="/grupos")
router.include_router(teacher_subject.router, prefix="/asignaciones-docentes")
router.include_router(student.router, prefix="/estudiantes")
router.include_router(research.router, prefix="/investigacion")

