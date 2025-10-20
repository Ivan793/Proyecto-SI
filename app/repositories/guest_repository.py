from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)

class GuestRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.INVITADOS, "id_invitado")

    async def get_guest_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener invitado por el id del usuario relacionado"""
        return await self.get_by_field("id_usuario", user_id)

    async def get_guests_by_sector(self, sector_id: str) -> List[Dict[str, Any]]:
        """Obtener todos los invitados de un sector específico"""
        return await self.get_all(filters={"id_sector": sector_id})

    async def get_guests_by_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Obtener todos los invitados de una empresa específica"""
        return await self.get_all(filters={"nombre_empresa": company_name})

    async def get_active_guests(self) -> List[Dict[str, Any]]:
        """Opcional: si se maneja un campo activo"""
        return await self.get_all(filters={"activo": True})
