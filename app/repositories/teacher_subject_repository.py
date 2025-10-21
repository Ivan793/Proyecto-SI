from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class TeacherSubjectRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.DOCENTE_MATERIAS, "id_docente_materia")

    async def get_assignments_by_teacher(self, teacher_id: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"id_docente": teacher_id})

    async def get_assignments_by_subject(self, subject_code: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"codigo_materia": subject_code})

    async def get_assignments_by_group(self, group_code: int) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"codigo_grupo": group_code})

    async def get_assignment_by_teacher_subject_group(
        self, 
        teacher_id: str, 
        subject_code: str, 
        group_code: int
    ) -> Optional[Dict[str, Any]]:
        assignments = await self.get_all(filters={
            "id_docente": teacher_id,
            "codigo_materia": subject_code,
            "codigo_grupo": group_code
        })
        return assignments[0] if assignments else None

    async def teacher_has_assignments(self, teacher_id: str) -> bool:
        assignments = await self.get_assignments_by_teacher(teacher_id)
        return len(assignments) > 0

    async def subject_has_assignments(self, subject_code: str) -> bool:
        assignments = await self.get_assignments_by_subject(subject_code)
        return len(assignments) > 0