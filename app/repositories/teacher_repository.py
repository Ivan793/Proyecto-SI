from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class TeacherRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.DOCENTES, "id_docente")

    async def get_teachers_by_program(self, program_code: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"codigo_programa": program_code})

    async def get_active_teachers(self) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"activo": True})

    async def get_teacher_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.get_by_field("id_usuario", user_id)