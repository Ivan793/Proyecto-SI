from typing import Optional, List, Dict, Any
import logging
from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class GraduateRepository(BaseRepository):
    def __init__(self):
        super().__init__(Collections.EGRESADOS, "id_egresado")

    async def get_active_graduates(self) -> List[Dict[str, Any]]:
        try:
            return await self.get_all(filters={"activo": True})
        except Exception as e:
            logger.error(f"Error al obtener egresados activos: {e}")
            return []

    async def get_graduate_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.get_by_field("id_usuario", user_id)
        except Exception as e:
            logger.error(f"Error al obtener egresado por usuario {user_id}: {e}")
            return None

    async def get_all_paginated(self, filters: Optional[Dict[str, Any]] = None, page: int = 1, limit: int = 20):
        try:
            all_data = await self.get_all(filters)
            total = len(all_data)
            start = (page - 1) * limit
            end = start + limit
            return all_data[start:end], total
        except Exception as e:
            logger.error(f"Error al obtener egresados paginados: {e}")
            return [], 0
