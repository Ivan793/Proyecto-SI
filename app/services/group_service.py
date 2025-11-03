from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

from app.repositories.group_repository import GroupRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupWithDetailsResponse
from app.exceptions.group_exceptions import (
    GroupNotFoundException,
    GroupAlreadyExistsException,
    GroupHasDependenciesException
)
from app.exceptions.subject_exceptions import SubjectNotFoundException
from app.exceptions.teacher_exceptions import TeacherNotFoundException
from app.exceptions.base_exceptions import ValidationException

logger = logging.getLogger(__name__)


class GroupService:

    def __init__(self):
        self.group_repo = GroupRepository()
        self.subject_repo = SubjectRepository()
        self.teacher_repo = TeacherRepository()

    async def create_group(
            self,
            group_data: GroupCreate,
            created_by: str
    ) -> GroupResponse:
        """
        Crear grupo con docente asignado (sin materia inicialmente).
        La materia se asigna después.
        """

        # Validar que el docente existe y está activo
        teacher = await self.teacher_repo.get_by_id(group_data.id_docente)
        if not teacher:
            raise TeacherNotFoundException(group_data.id_docente)

        if not teacher.get("activo", True):
            raise ValidationException(
                message=f"El docente {group_data.id_docente} no está activo",
                field="id_docente"
            )

        # Verificar si el grupo ya existe
        existing_group = await self.group_repo.get_by_id(group_data.codigo_grupo)
        if existing_group:
            raise GroupAlreadyExistsException(group_data.codigo_grupo)

        # Crear el grupo
        group_dict = group_data.model_dump()
        group_dict.update({
            "activo": True,
            "created_at": datetime.now(timezone.utc),
            "created_by": created_by,
        })

        await self.group_repo.create(group_dict, group_data.codigo_grupo)

        # Obtener grupo creado
        created_group = await self.group_repo.get_by_id(group_data.codigo_grupo)
        return GroupResponse(**created_group)

    async def get_group(self, group_code: str) -> GroupResponse:
        """Obtener grupo por código"""
        group = await self.group_repo.get_by_id(group_code)
        if not group:
            raise GroupNotFoundException(group_code)
        return GroupResponse(**group)

    async def get_group_with_details(self, group_code: str) -> GroupWithDetailsResponse:
        """Obtener grupo con información completa de materia y docente"""
        try:
            group_with_details = await self.group_repo.get_group_with_details(group_code)

            if not group_with_details:
                raise GroupNotFoundException(group_code)

            return GroupWithDetailsResponse(**group_with_details)

        except Exception as e:
            logger.error(f"Error en get_group_with_details para grupo {group_code}: {str(e)}")
            raise

    async def get_all_groups(
            self,
            active_only: bool = True,
            subject_code: Optional[str] = None,
            teacher_id: Optional[str] = None,
            page: int = 1,
            limit: int = 20
    ) -> tuple[List[GroupWithDetailsResponse], int]:
        """Obtener todos los grupos con filtros opcionales"""

        try:
            filters = {"activo": True} if active_only else {}

            # Aplicar filtros específicos
            if subject_code:
                filters["codigo_materia"] = subject_code

            if teacher_id:
                filters["id_docente"] = teacher_id

            # Obtener grupos
            groups_data = await self.group_repo.get_all(filters=filters)

            # Obtener detalles completos para cada grupo
            groups_with_details = []
            for group in groups_data:
                try:
                    group_code = group.get("codigo_grupo")
                    if not group_code:
                        continue

                    group_details = await self.get_group_with_details(group_code)
                    if group_details:
                        groups_with_details.append(group_details)

                except GroupNotFoundException:
                    continue
                except Exception as e:
                    logger.error(f"Error obteniendo detalles del grupo {group.get('codigo_grupo')}: {str(e)}")
                    continue

            # Aplicar paginación
            total = len(groups_with_details)
            start = (page - 1) * limit
            end = start + limit
            paginated_groups = groups_with_details[start:end]

            return paginated_groups, total

        except Exception as e:
            logger.error(f"Error en get_all_groups: {str(e)}", exc_info=True)
            return [], 0

    async def update_group(
            self,
            group_code: str,
            group_data: GroupUpdate
    ) -> GroupResponse:
        """Actualizar grupo"""
        group = await self.group_repo.get_by_id(group_code)
        if not group:
            raise GroupNotFoundException(group_code)

        update_dict = group_data.model_dump(exclude_none=True)

        if not update_dict:
            return await self.get_group(group_code)

        # Si se cambia el docente, validar que existe y está activo
        if 'id_docente' in update_dict:
            teacher = await self.teacher_repo.get_by_id(update_dict['id_docente'])
            if not teacher:
                raise TeacherNotFoundException(update_dict['id_docente'])
            if not teacher.get("activo", True):
                raise ValidationException(
                    message=f"El docente {update_dict['id_docente']} no está activo",
                    field="id_docente"
                )

        # Si se cambia la materia, validar que existe y actualizar ambas direcciones
        if 'codigo_materia' in update_dict:
            new_subject_code = update_dict['codigo_materia']
            old_subject_code = group.get('codigo_materia')

            # Si se está cambiando de materia
            if new_subject_code != old_subject_code:
                # Validar que la nueva materia existe
                if new_subject_code:
                    subject = await self.subject_repo.get_by_id(new_subject_code)
                    if not subject:
                        raise SubjectNotFoundException(new_subject_code)

                # Remover de la materia anterior si existía
                if old_subject_code:
                    await self.subject_repo.remove_group_from_subject_list(old_subject_code, group_code)

                # Agregar a la nueva materia
                if new_subject_code:
                    await self.subject_repo.add_group_to_subject_list(new_subject_code, group_code)

        # Actualizar
        await self.group_repo.update(group_code, update_dict)
        updated_group = await self.group_repo.get_by_id(group_code)

        return GroupResponse(**updated_group)

    async def assign_subject_to_group(
            self,
            group_code: str,
            subject_code: str
    ) -> GroupResponse:
        """Asignar materia a un grupo existente"""

        group = await self.group_repo.get_by_id(group_code)
        if not group:
            raise GroupNotFoundException(group_code)

        # Verificar que la materia existe
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Si el grupo ya tiene una materia, removerlo de esa materia
        current_subject = group.get('codigo_materia')
        if current_subject:
            await self.subject_repo.remove_group_from_subject_list(current_subject, group_code)

        # Asignar materia al grupo
        await self.group_repo.update(group_code, {
            "codigo_materia": subject_code,
            "updated_at": datetime.now(timezone.utc)
        })

        # Agregar el grupo a la materia
        await self.subject_repo.add_group_to_subject_list(subject_code, group_code)

        updated_group = await self.group_repo.get_by_id(group_code)
        return GroupResponse(**updated_group)

    async def deactivate_group(self, group_code: str, reason: str) -> bool:
        """Desactivar grupo"""
        group = await self.group_repo.get_by_id(group_code)
        if not group:
            raise GroupNotFoundException(group_code)

        # Si el grupo tiene una materia asignada, removerlo de esa materia
        current_subject = group.get('codigo_materia')
        if current_subject:
            await self.subject_repo.remove_group_from_subject_list(current_subject, group_code)

        return await self.group_repo.update(group_code, {
            "activo": False,
            "razon_desactivacion": reason,
            "codigo_materia": None  # Desasignar la materia al desactivar
        })

    async def activate_group(self, group_code: str) -> bool:
        """Activar grupo"""
        group = await self.group_repo.get_by_id(group_code)
        if not group:
            raise GroupNotFoundException(group_code)

        return await self.group_repo.update(group_code, {
            "activo": True,
            "razon_desactivacion": None
        })

    async def get_groups_by_subject(self, subject_code: str) -> List[GroupWithDetailsResponse]:
        """Obtener grupos por materia"""
        groups = await self.group_repo.get_groups_by_subject(subject_code)

        enriched_groups = []
        for group in groups:
            group_code = group.get("codigo_grupo")
            if group_code:
                group_details = await self.get_group_with_details(group_code)
                if group_details:
                    enriched_groups.append(group_details)

        return enriched_groups

    async def get_groups_by_teacher(self, teacher_id: str) -> List[GroupWithDetailsResponse]:
        """Obtener grupos por docente"""
        groups = await self.group_repo.get_groups_by_teacher(teacher_id)

        enriched_groups = []
        for group in groups:
            group_code = group.get("codigo_grupo")
            if group_code:
                group_details = await self.get_group_with_details(group_code)
                if group_details:
                    enriched_groups.append(group_details)

        return enriched_groups

    async def get_groups_without_subject(self) -> List[GroupResponse]:
        """Obtener grupos que no tienen materia asignada"""
        groups = await self.group_repo.get_groups_without_subject()
        return [GroupResponse(**group) for group in groups]