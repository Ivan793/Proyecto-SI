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
    
    # async def get_teacher_by_user_id2(self, user_id: str):
    #     """
    #     Busca un profesor por su ID de usuario asociado.
    #     """
    #     query = self.collection.where("user_id", "==", user_id)
    #     results = await query.get()
    #     if not results:
    #         return None
    #     return results[0].to_dict(), "Perfil actualizado correctamente"