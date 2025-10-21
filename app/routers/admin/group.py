from fastapi import APIRouter, Body, Depends, Query, status, Request
from typing import Optional, Dict, Any
import logging

from app.schemas.types import ReasonText
from app.services.group_service import GroupService
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupWithSubjectResponse
from app.schemas.common import PaginationParams

from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response
)
from app.exceptions.group_exceptions import (
    GroupNotFoundException, 
    GroupAlreadyExistsException,
    GroupHasDependenciesException,
    SubjectNotFoundException,
    TeacherNotFoundException
)
from app.exceptions.assignment_exceptions import TeacherNotAvailableException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Grupos - Admin"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo grupo",
    description="Crea un nuevo grupo asignado a una materia y un profesor"
)
@admin_rate_limit()
async def create_group(
    request: Request,
    group_data: GroupCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        subject_code = group_data.codigo_materia
        group = await service.create_group(group_data,subject_code, current_admin["user_id"])
        
        logger.info(f"Grupo creado: {group.codigo_grupo} por {current_admin['nombre_completo']}")
        
        return created_response(
            data=group.model_dump(),
            message="Grupo creado exitosamente"
        )
        
    except GroupAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except SubjectNotFoundException as e:
        return not_found_response("Materia", group_data.codigo_materia)
    except TeacherNotFoundException as e:
        return not_found_response("Profesor", group_data.id_docente)
    except TeacherNotAvailableException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error inesperado creando grupo: {str(e)}")
        return internal_server_error_response()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar todos los grupos",
    description="Obtiene la lista de grupos con opciones de filtrado y paginación"
)
@admin_rate_limit()
async def get_groups(
    request: Request,
    activos: bool = Query(True, description="Filtrar solo grupos activos"),
    materia: Optional[str] = Query(None, description="Filtrar por código de materia"),
    profesor: Optional[str] = Query(None, description="Filtrar por ID de profesor"),
    params: PaginationParams = Depends(),
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        groups, total = await service.get_all_groups(
            active_only=activos,
            subject_code=materia,
            teacher_id=profesor,
            page=params.page,
            limit=params.limit
        )

        return paginated_response(
            data=[group.model_dump() for group in groups],
            page=params.page,
            limit=params.limit,
            total_items=total
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{group_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupo por código",
    description="Obtiene información detallada de un grupo específico"
)
@admin_rate_limit()
async def get_group_by_code(
    request: Request,
    group_code: int,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        group = await service.get_group(group_code)
        
        return success_response(
            data=group.model_dump(),
            message="Grupo obtenido correctamente"
        )
        
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except Exception as e:
        logger.error(f"Error obteniendo grupo {group_code}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{group_code}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupo con detalles completos",
    description="Obtiene información completa del grupo incluyendo materia y profesor"
)
@admin_rate_limit()
async def get_group_with_details(
    request: Request,
    group_code: int,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        group_with_details = await service.get_group_with_details(group_code)
        
        return success_response(
            data=group_with_details.model_dump(),
            message="Grupo con detalles obtenido correctamente"
        )
        
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except Exception as e:
        logger.error(f"Error obteniendo grupo completo {group_code}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{group_code}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar grupo",
    description="Actualiza la información de un grupo existente"
)
@admin_rate_limit()
async def update_group(
    request: Request,
    group_code: int,
    group_data: GroupUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        group = await service.update_group(group_code, group_data)
        
        logger.info(f"Grupo actualizado: {group_code} por {current_admin['nombre_completo']}")
        
        return updated_response(
            data=group.model_dump(),
            message="Grupo actualizado exitosamente"
        )
        
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except SubjectNotFoundException as e:
        return not_found_response("Materia", group_data.codigo_materia)
    except TeacherNotFoundException as e:
        return not_found_response("Profesor", group_data.id_docente)
    except TeacherNotAvailableException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando grupo {group_code}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/materia/{subject_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupos por materia",
    description="Obtiene todos los grupos asociados a una materia específica"
)
@admin_rate_limit()
async def get_groups_by_subject(
    request: Request,
    subject_code: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        groups = await service.get_groups_by_subject(subject_code)
        
        return success_response(
            data=[group.model_dump() for group in groups],
            message=f"Grupos de la materia {subject_code} obtenidos correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos de materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/profesor/{teacher_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupos por profesor",
    description="Obtiene todos los grupos asignados a un profesor específico"
)
@admin_rate_limit()
async def get_groups_by_teacher(
    request: Request,
    teacher_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        groups = await service.get_groups_by_teacher(teacher_id)
        
        return success_response(
            data=[group.model_dump() for group in groups],
            message=f"Grupos del profesor {teacher_id} obtenidos correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos del profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{group_code}/desactivar",
    status_code=status.HTTP_200_OK,
    summary="Desactivar grupo",
    description="Desactiva un grupo de forma lógica (no elimina el registro)"
)
@admin_rate_limit()
async def deactivate_group(
    request: Request,
    group_code: int,
    razon: ReasonText = Body(..., embed=True),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = GroupService()
        success = await service.deactivate_group(group_code, razon)
        
        if success:
            logger.info(f"Grupo desactivado: {group_code} por {current_admin['nombre_completo']}")
            return success_response(
                data={"desactivado": True},
                message="Grupo desactivado exitosamente"
            )
        else:
            return bad_request_response(
                message="No se pudo desactivar el grupo"
            )
            
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except GroupHasDependenciesException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error desactivando grupo {group_code}: {str(e)}")
        return internal_server_error_response()