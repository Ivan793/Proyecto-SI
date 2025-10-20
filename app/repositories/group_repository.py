from typing import Optional, List, Dict, Any
import logging

from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_subject_repository import TeacherSubjectRepository

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class GroupRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.GRUPOS, "codigo_grupo")

    async def get_groups_by_subject(self, subject_code: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"codigo_materia": subject_code})

    async def get_groups_by_teacher(self, teacher_id: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"id_docente": teacher_id})

    async def get_active_groups(self) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"activo": True})

    async def group_has_students(self, group_code: int) -> bool:
        # Verificar si el grupo tiene estudiantes inscritos
        from app.repositories.teacher_subject_repository import TeacherSubjectRepository
        ts_repo = TeacherSubjectRepository()
        assignments = await ts_repo.get_assignments_by_group(group_code)
        return len(assignments) > 0

    async def get_group_with_details(self, group_code: int) -> Optional[Dict[str, Any]]:
        group = await self.get_by_id(str(group_code))
        if not group:
            return None

        # Obtener información de la materia
        subject_repo = SubjectRepository()
        subject_info = await subject_repo.get_by_id(group.get("codigo_materia", ""))

        # Obtener docentes asignados desde TeacherSubject
        ts_repo = TeacherSubjectRepository()
        assignments = await ts_repo.get_assignments_by_group(group_code)
        
        group["materia_info"] = subject_info
        group["nombre_materia"] = subject_info.get("nombre_materia") if subject_info else None
        group["docentes_asignados"] = assignments  # ← Esta es la fuente verdadera
        
        return group