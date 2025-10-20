from typing import List, Dict, Any, Optional
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)

class SectorRepository(BaseRepository):

    def __init__(self):
        super().__init__(Collections.SECTORES, "id_sector")

    async def get_sector_by_name(self, nombre_sector: str) -> Optional[Dict[str, Any]]:
        return await self.get_by_field("nombre_sector", nombre_sector)
    
    async def get_all_sectors(self) -> List[Dict[str, Any]]:
        return await self.get_all()
