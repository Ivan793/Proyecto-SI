import asyncio
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

from app.repositories.subject_repository import SubjectRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.subject import (
    SubjectCreate, 
    SubjectWithGroupsCreate, 
    SubjectUpdate,
    SubjectResponse
)
from app.exceptions.subject_exceptions import (
    SubjectNotFoundException,
    SubjectAlreadyExistsException,
    SubjectHasDependenciesException,
    MinimumGroupsRequiredException
)
from app.exceptions.group_exceptions import GroupNotFoundException
from app.exceptions.teacher_exceptions import TeacherNotFoundException
from app.exceptions.base_exceptions import ValidationException

logger = logging.getLogger(__name__)


class SubjectService:
    
    def __init__(self):
        self.subject_repo = SubjectRepository()
        self.group_repo = GroupRepository()
        self.teacher_repo = TeacherRepository()

    async def create_subject_simple(
        self,
        subject_data: SubjectCreate,
        created_by: str
    ) -> SubjectResponse:
        """Crear materia SIN grupos"""
        
        # Verificar que no exista
        existing = await self.subject_repo.get_by_id(subject_data.codigo_materia)
        if existing:
            raise SubjectAlreadyExistsException(subject_data.codigo_materia)
        
        # Crear materia con lista vacía de grupos
        subject_dict = subject_data.model_dump()
        subject_dict.update({
            "created_at": datetime.now(timezone.utc),
            "created_by": created_by,
            "activo": True,
            "grupos_asignados": []  # Inicializar lista vacía
        })
        
        await self.subject_repo.create(subject_dict, subject_data.codigo_materia)
        
        created_subject = await self.subject_repo.get_by_id(subject_data.codigo_materia)
        return SubjectResponse(**created_subject)

    async def create_subject_with_groups(
        self,
        subject_with_groups: SubjectWithGroupsCreate,
        created_by: str
    ) -> SubjectResponse:
        """
        Crear materia Y asignar grupos existentes.
        Los grupos DEBEN existir previamente.
        """
        
        subject_data = subject_with_groups.materia
        group_codes = subject_with_groups.codigos_grupo
        
        # Validar mínimo de grupos
        if not group_codes or len(group_codes) == 0:
            raise MinimumGroupsRequiredException()
        
        # Verificar que la materia NO exista
        existing = await self.subject_repo.get_by_id(subject_data.codigo_materia)
        if existing:
            raise SubjectAlreadyExistsException(subject_data.codigo_materia)
        
        # Verificar que todos los grupos existen
        await self._validate_groups_exist(group_codes)
        
        # Crear la materia con la lista de grupos
        subject_dict = subject_data.model_dump()
        subject_dict.update({
            "created_at": datetime.now(timezone.utc),
            "created_by": created_by,
            "activo": True,
            "grupos_asignados": group_codes  # Incluir grupos desde el inicio
        })
        
        await self.subject_repo.create(subject_dict, subject_data.codigo_materia)
        
        # Asignar grupos a la materia (actualizar cada grupo)
        await self._assign_groups_to_subject(group_codes, subject_data.codigo_materia)
        
        # Retornar materia con grupos asignados
        created_subject = await self.subject_repo.get_by_id(subject_data.codigo_materia)
        return SubjectResponse(**created_subject)

    async def _validate_groups_exist(self, group_codes: List[str]):
        """Validar que todos los grupos existan"""
        
        check_tasks = [
            self.group_repo.get_by_id(code) 
            for code in group_codes
        ]
        groups = await asyncio.gather(*check_tasks)
        
        # Encontrar grupos que no existen
        missing = [
            group_codes[i] 
            for i, group in enumerate(groups) 
            if group is None
        ]
        
        if missing:
            raise GroupNotFoundException(missing[0])

    async def _assign_groups_to_subject(
        self, 
        group_codes: List[str], 
        subject_code: str
    ):
        """Asignar materia a múltiples grupos"""
        
        update_tasks = [
            self.group_repo.update(code, {
                "codigo_materia": subject_code,
                "updated_at": datetime.now(timezone.utc)
            })
            for code in group_codes
        ]
        
        await asyncio.gather(*update_tasks)

    async def get_subject(self, subject_code: str) -> SubjectResponse:
        """Obtener materia por código"""
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        return SubjectResponse(**subject)

    async def get_subject_with_groups(self, subject_code: str) -> Dict[str, Any]:
        """Obtener materia con grupos y docentes"""
        subject_with_groups = await self.subject_repo.get_subject_with_groups(subject_code)
        if not subject_with_groups:
            raise SubjectNotFoundException(subject_code)
        
        return subject_with_groups

    async def get_all_subjects(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[SubjectResponse], int]:
        """Obtener todas las materias"""
        filters = {"activo": True} if active_only else {}
        subjects = await self.subject_repo.get_all(filters=filters)
        
        total = len(subjects)
        start = (page - 1) * limit
        end = start + limit
        paginated_subjects = subjects[start:end]
        
        return [SubjectResponse(**subject) for subject in paginated_subjects], total

    async def update_subject(
        self, 
        subject_code: str, 
        subject_data: SubjectUpdate
    ) -> SubjectResponse:
        """Actualizar materia"""
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        update_dict = subject_data.model_dump(exclude_none=True)
        if update_dict:
            await self.subject_repo.update(subject_code, update_dict)

        updated_subject = await self.subject_repo.get_by_id(subject_code)
        return SubjectResponse(**updated_subject)

    async def add_group_to_subject(
        self, 
        subject_code: str, 
        group_code: str
    ) -> bool:
        """Agregar un grupo existente a una materia"""
        
        # Verificar que la materia existe
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        
        # Verificar que el grupo existe
        group = await self.group_repo.get_by_id(group_code)
        if not group:
            raise GroupNotFoundException(group_code)
        
        # Verificar si el grupo ya está asignado a otra materia
        current_subject = group.get("codigo_materia")
        if current_subject and current_subject != subject_code:
            raise ValidationException(
                message=f"El grupo {group_code} ya está asignado a la materia {current_subject}",
                field="grupo"
            )
        
        # Asignar materia al grupo
        await self.group_repo.update(group_code, {
            "codigo_materia": subject_code,
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Agregar el grupo a la lista de grupos de la materia
        await self.subject_repo.add_group_to_subject_list(subject_code, group_code)
        
        return True

    async def add_groups_to_subject(
        self,
        subject_code: str,
        group_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Agregar MÚLTIPLES grupos a una materia.
        Retorna resumen de la operación.
        """
        
        # Verificar que la materia existe
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        
        # Validar que todos los grupos existen
        await self._validate_groups_exist(group_codes)
        
        # Asignar grupos a la materia
        await self._assign_groups_to_subject(group_codes, subject_code)
        
        # Actualizar la lista de grupos en la materia
        await self.subject_repo.update_subject_groups(subject_code, group_codes)
        
        return {
            "materia": subject_code,
            "grupos_asignados": group_codes,
            "total": len(group_codes)
        }

    async def remove_group_from_subject(
        self,
        subject_code: str,
        group_code: str
    ) -> bool:
        """Desasignar grupo de una materia"""
        
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        
        group = await self.group_repo.get_by_id(group_code)
        if not group:
            raise GroupNotFoundException(group_code)
        
        # Remover materia del grupo
        await self.group_repo.update(group_code, {
            "codigo_materia": None,
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Remover el grupo de la lista de grupos de la materia
        await self.subject_repo.remove_group_from_subject_list(subject_code, group_code)
        
        return True

    async def deactivate_subject(self, subject_code: str, reason: str) -> bool:
        """Desactivar materia"""
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Verificar si la materia tiene grupos activos
        if await self.subject_repo.subject_has_groups(subject_code):
            raise SubjectHasDependenciesException(
                subject_code,
                dependencies={"grupos_activos": True}
            )

        return await self.subject_repo.update(subject_code, {
            "activo": False,
            "razon_desactivacion": reason
        })
    
    async def activate_subject(self, subject_code: str) -> bool:
        """Activar materia"""
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        return await self.subject_repo.update(subject_code, {
            "activo": True,
            "razon_desactivacion": None
        })

    async def get_teachers_for_subject(self, subject_code: str) -> List[Dict[str, Any]]:
        """Obtener docentes asignados a una materia"""
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        
        return await self.subject_repo.get_teachers_for_subject(subject_code)