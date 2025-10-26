from typing import Optional, List, Dict, Any
import logging
from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class GuestRepository(BaseRepository):
    def __init__(self):
        super().__init__(Collections.INVITADOS, "id_invitado")

    async def get_active_guests(self) -> List[Dict[str, Any]]:
        try:
            guests = await self.get_all(filters={"activo": True})
            logger.info(f"{len(guests)} invitados activos obtenidos.")
            return guests
        except Exception as e:
            logger.error(f"Error al obtener invitados activos: {e}")
            return []

    async def get_guest_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            guest = await self.get_by_field("id_usuario", user_id)
            if guest:
                logger.info(f"Invitado encontrado para usuario {user_id}.")
            else:
                logger.warning(f"No se encontró invitado para usuario {user_id}.")
            return guest
        except Exception as e:
            logger.error(f"Error al obtener invitado por usuario {user_id}: {e}")
            return None

    async def get_all_paginated(self, filters: Optional[Dict[str, Any]] = None, page: int = 1, limit: int = 20):
        try:
            all_data = await self.get_all(filters)
            total = len(all_data)
            start = (page - 1) * limit
            end = start + limit
            return all_data[start:end], total
        except Exception as e:
            logger.error(f"Error al obtener invitados paginados: {e}")
            return [], 0
