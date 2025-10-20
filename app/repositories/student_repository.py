from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)

class StudentRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.ESTUDIANTES, "id_estudiante")

    async def get_students_by_program(self, program_code: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"codigo_programa": program_code})

    async def get_active_students(self) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"activo": True})

    async def get_student_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.get_by_field("id_usuario", user_id)

    async def get_students_by_semester(self, semester: int) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"semestre": semester})

    async def get_students_by_admission_year(self, year: int) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"anio_ingreso": year})