from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class SubjectRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.MATERIAS, "codigo_materia")

    async def get_subjects_by_cycle(self, cycle: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"ciclo_semestral": cycle})

    async def get_active_subjects(self) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"activo": True})

    async def subject_has_groups(self, subject_code: str) -> bool:
        from app.repositories.group_repository import GroupRepository
        group_repo = GroupRepository()
        groups = await group_repo.get_groups_by_subject(subject_code)
        return len(groups) > 0

    async def get_subject_with_groups(self, subject_code: str) -> Optional[Dict[str, Any]]:
        subject = await self.get_by_id(subject_code)
        if not subject:
            return None

        from app.repositories.group_repository import GroupRepository
        group_repo = GroupRepository()
        groups = await group_repo.get_groups_by_subject(subject_code)
        
        subject["grupos"] = groups
        return subject