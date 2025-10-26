from typing import List, Optional, Dict, Any
import logging

from app.repositories.group_repository import GroupRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_subject_repository import TeacherSubjectRepository
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupWithSubjectResponse
from app.exceptions.group_exceptions import (
    GroupNotFoundException,
    GroupAlreadyExistsException,
    GroupHasDependenciesException,
    SubjectNotFoundException
)

logger = logging.getLogger(__name__)


class GroupService:
    
    def __init__(self):
        self.group_repo = GroupRepository()
        self.subject_repo = SubjectRepository()
        self.teacher_subject_repo = TeacherSubjectRepository()

    async def create_group(
        self, 
        group_data: GroupCreate, 
        subject_code: str,
        created_by: str
    ) -> GroupResponse:
        # Verificar si la materia existe
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Verificar si el grupo ya existe
        existing_group = await self.group_repo.get_by_id(str(group_data.codigo_grupo))
        if existing_group:
            raise GroupAlreadyExistsException(group_data.codigo_grupo)

        # Crear el grupo (sin docente)
        group_dict = group_data.model_dump()
        group_dict.update({
            "codigo_materia": subject_code,
            "activo": True,
            "created_by": created_by
        })
        
        group_id = str(group_data.codigo_grupo)
        await self.group_repo.create(group_dict, group_id)

        # Obtener el grupo creado con detalles
        group_with_details = await self.group_repo.get_group_with_details(group_data.codigo_grupo)
        return GroupWithSubjectResponse(**group_with_details)

    async def get_group(self, group_code: int) -> GroupResponse:
        group = await self.group_repo.get_by_id(str(group_code))
        if not group:
            raise GroupNotFoundException(group_code)
        return GroupResponse(**group)

    async def get_group_with_details(self, group_code: int) -> GroupWithSubjectResponse:
        try:
            # Asegurar que group_code sea string para la búsqueda
            group_id = str(group_code)
            group_with_details = await self.group_repo.get_group_with_details(group_code)
            
            if not group_with_details:
                raise GroupNotFoundException(group_code)
            
            # Asegurar tipos de datos
            if "codigo_grupo" in group_with_details and isinstance(group_with_details["codigo_grupo"], str):
                try:
                    group_with_details["codigo_grupo"] = int(group_with_details["codigo_grupo"])
                except ValueError:
                    pass
            
            return GroupWithSubjectResponse(**group_with_details)
            
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
    ) -> tuple[List[GroupWithSubjectResponse], int]:

        try:
            # Obtener todos los grupos primero
            filters = {"activo": True} if active_only else {}
            groups_data = await self.group_repo.get_all(filters=filters)
            
            # Si se filtra por docente, obtener grupos desde TeacherSubject
            if teacher_id:
                assignments = await self.teacher_subject_repo.get_assignments_by_teacher(teacher_id)
                
                # Filtrar solo asignaciones activas si active_only es True
                if active_only:
                    assignments = [a for a in assignments if a.get("activo", True)]
                
                # Extraer códigos de grupo únicos
                group_codes = set()
                for assignment in assignments:
                    group_code = assignment.get("codigo_grupo")
                    if group_code is not None:
                        # Asegurar que group_code sea int
                        if isinstance(group_code, str):
                            try:
                                group_code = int(group_code)
                            except ValueError:
                                continue
                        group_codes.add(group_code)
                
                # Filtrar grupos por los códigos encontrados
                filtered_groups = []
                for group in groups_data:
                    group_code = group.get("codigo_grupo")
                    if group_code in group_codes:
                        filtered_groups.append(group)
                
                groups_data = filtered_groups
            
            # Filtrar por materia si se especifica
            if subject_code:
                groups_data = [group for group in groups_data if group.get("codigo_materia") == subject_code]
            
            # Obtener detalles completos para cada grupo
            groups_with_details = []
            for group in groups_data:
                try:
                    group_code = group.get("codigo_grupo")
                    if group_code is None:
                        continue
                        
                    group_details = await self.get_group_with_details(group_code)
                    if group_details:
                        groups_with_details.append(group_details)
                except GroupNotFoundException:
                    # Si el grupo no existe, continuar con el siguiente
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
        group_code: int, 
        group_data: GroupUpdate
    ) -> GroupResponse:
        group = await self.group_repo.get_by_id(str(group_code))
        if not group:
            raise GroupNotFoundException(group_code)

        update_dict = group_data.model_dump(exclude_none=True)
        
        if not update_dict:
            # Si no hay cambios, devolver el grupo actual
            return await self.get_group(group_code)

        # Manejar cambio de código de grupo (requiere operación especial)
        new_group_code = update_dict.get('codigo_grupo')
        is_changing_group_code = new_group_code is not None and new_group_code != group_code

        if is_changing_group_code:
            # Verificar que el nuevo código no exista
            existing_group = await self.group_repo.get_by_id(str(new_group_code))
            if existing_group:
                raise GroupAlreadyExistsException(new_group_code)
            
            # Crear nuevo documento con el nuevo código
            new_group_data = group.copy()
            new_group_data.update(update_dict)
            await self.group_repo.create(new_group_data, str(new_group_code))
            
            # Actualizar todas las asignaciones en teacher_subject
            assignments = await self.teacher_subject_repo.get_assignments_by_group(group_code)
            for assignment in assignments:
                await self.teacher_subject_repo.update(
                    assignment["id_docente_materia"],
                    {"codigo_grupo": new_group_code}
                )
            
            # Eliminar el documento antiguo
            await self.group_repo.delete(str(group_code))
            
            # Obtener el grupo recién creado
            updated_group = await self.group_repo.get_by_id(str(new_group_code))
            
        else:
            # Actualización normal sin cambiar el código de grupo
            # Si se cambia la materia, validar que existe
            if 'codigo_materia' in update_dict and update_dict['codigo_materia']:
                subject = await self.subject_repo.get_by_id(update_dict['codigo_materia'])
                if not subject:
                    raise SubjectNotFoundException(update_dict['codigo_materia'])
                
                # Verificar y actualizar asignaciones existentes
                assignments = await self.teacher_subject_repo.get_assignments_by_group(group_code)
                active_assignments = [a for a in assignments if a.get("activo", True)]
                
                if active_assignments:
                    # Actualizar todas las asignaciones activas a la nueva materia
                    for assignment in active_assignments:
                        await self.teacher_subject_repo.update(
                            assignment["id_docente_materia"],
                            {"codigo_materia": update_dict['codigo_materia']}
                        )

            # Actualizar el documento existente
            await self.group_repo.update(str(group_code), update_dict)
            updated_group = await self.group_repo.get_by_id(str(group_code))

        return GroupResponse(**updated_group)

    async def deactivate_group(self, group_code: int, reason: str) -> bool:
        group = await self.group_repo.get_by_id(str(group_code))
        if not group:
            raise GroupNotFoundException(group_code)

        # Verificar si el grupo tiene asignaciones activas
        assignments = await self.teacher_subject_repo.get_assignments_by_group(group_code)
        active_assignments = [a for a in assignments if a.get("activo", True)]
        
        if active_assignments:
            raise GroupHasDependenciesException(
                group_code,
                dependencies={"asignaciones_activas": len(active_assignments)}
            )

        return await self.group_repo.update(str(group_code), {
            "activo": False,
            "razon_desactivacion": reason
        })

    async def get_groups_by_subject(self, subject_code: str) -> List[GroupWithSubjectResponse]:
        groups_with_details = await self.group_repo.get_groups_by_subject(subject_code)
        
        # Enriquecer con información de docentes
        enriched_groups = []
        for group in groups_with_details:
            group_details = await self.get_group_with_details(group["codigo_grupo"])
            if group_details:
                enriched_groups.append(group_details)
            
        return enriched_groups

    async def get_groups_by_teacher(self, teacher_id: str) -> List[GroupWithSubjectResponse]:
        # Obtener asignaciones del docente
        assignments = await self.teacher_subject_repo.get_assignments_by_teacher(teacher_id)
        active_assignments = [a for a in assignments if a.get("activo", True)]
        
        # Obtener detalles de los grupos
        groups_with_details = []
        for assignment in active_assignments:
            group_details = await self.get_group_with_details(assignment["codigo_grupo"])
            if group_details:
                groups_with_details.append(group_details)
                
        return groups_with_details

    async def get_group_assignments(self, group_code: int) -> List[Dict[str, Any]]:
        """Obtiene todas las asignaciones de docentes para un grupo"""
        group = await self.group_repo.get_by_id(str(group_code))
        if not group:
            raise GroupNotFoundException(group_code)
            
        assignments = await self.teacher_subject_repo.get_assignments_by_group(group_code)
        return assignments