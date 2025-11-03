from fastapi import APIRouter, Body, Depends, Query, status, Request, HTTPException
from typing import Optional, Dict, Any, List
import logging

from app.schemas.types import ReasonText
from app.services.group_service import GroupService
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupWithDetailsResponse
from app.schemas.common import PaginationParams

from app.dependencies.auth_dependencies import (
    get_authenticated_user, 
    get_current_admin_user,
    require_admin,
    require_admin_or_teacher,
    require_any_authenticated
)
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response,
    message_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.group_exceptions import (
    GroupNotFoundException, 
    GroupAlreadyExistsException,
    GroupHasDependenciesException,
    SubjectNotFoundException,
    TeacherNotFoundException
)
from app.exceptions.base_exceptions import ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Grupos-Admin (Otros Roles)"])


# ENDPOINTS PARA TODOS LOS ROLES AUTENTICADOS

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar grupos disponibles",
    description=(
        "**Disponible para:** Todos los Roles.\n\n"
        "Permite listar todos los grupos con opciones de filtrado (por materia, profesor, o estado activo)."
    ),
    responses=ResponseDocumentation.get_paginated_response()
)
async def get_groups(
    request: Request,
    activos: bool = Query(True, description="Filtrar solo grupos activos"),
    materia: Optional[str] = Query(None, description="Filtrar por código de materia"),
    profesor: Optional[str] = Query(None, description="Filtrar por ID de profesor"),
    params: PaginationParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_any_authenticated)
):
    """
    Permite a cualquier usuario autenticado (Estudiante, Profesor, Admin) listar grupos
    """
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
            total_items=total,
            message="Grupos obtenidos exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{group_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener información básica de grupo",
    description=("**Disponible para:** Todos los Roles.\n\n"
        "Obtiene información básica de un grupo específico"),
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_group_by_code(
    request: Request,
    group_code: str,
    current_user: Dict[str, Any] = Depends(require_any_authenticated)
):
    """
    Permite a cualquier usuario autenticado ver información básica de un grupo
    """
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
    "/materia/{subject_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupos por materia",
    description=("**Disponible para:** Todos los Roles.\n\n"
        "Obtiene todos los grupos asociados a una materia específica"),
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_groups_by_subject(
    request: Request,
    subject_code: str,
    current_user: Dict[str, Any] = Depends(require_any_authenticated)
):
    """
    Permite a cualquier usuario autenticado buscar grupos por materia
    """
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



# ENDPOINTS PARA PROFESORES Y ADMINISTRADORES

@router.get(
    "/profesor/{teacher_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupos por profesor",
    description=("**Disponible para:** Profesores y Administradores.\n\n"
        "Obtiene todos los grupos asignados a un profesor específico"),
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_groups_by_teacher(
    request: Request,
    teacher_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_or_teacher)
):
    """
    Permite a administradores y profesores ver grupos por profesor.
    Los profesores solo pueden ver sus propios grupos.
    """
    try:
        # Validación adicional: Profesores solo pueden ver sus propios grupos
        user_role = current_user.get("rol")
        user_id = current_user.get("user_id")
        
        if user_role == "Docente" and teacher_id != user_id:
            return bad_request_response(message="Solo puedes ver tus propios grupos")
        
        service = GroupService()
        groups = await service.get_groups_by_teacher(teacher_id)
        
        return success_response(
            data=[group.model_dump() for group in groups],
            message=f"Grupos del profesor {teacher_id} obtenidos correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos del profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{group_code}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupo con detalles completos",
    description=("**Disponible para:** Profesores y Administradores.\n\n"
        "Obtiene información completa del grupo incluyendo materia y profesor"),
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_group_with_details(
    request: Request,
    group_code: str,
    current_user: Dict[str, Any] = Depends(require_admin_or_teacher)
):
    """
    Permite a administradores y profesores ver información completa de grupos
    """
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



# ENDPOINTS EXCLUSIVOS PARA ADMINISTRADORES


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo grupo",
    description=("**Disponible para:** Solo Administradores.\n\n"
        "Crea un nuevo grupo asignado a un profesor (sin materia inicialmente)"),
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_group(
    request: Request,
    group_data: GroupCreate,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Solo administradores pueden crear nuevos grupos
    """
    try:
        service = GroupService()
        group = await service.create_group(group_data, current_admin["user_id"])
        
        logger.info(f"Grupo creado: {group.codigo_grupo} por {current_admin['nombre_completo']}")
        
        return created_response(
            data=group.model_dump(),
            message="Grupo creado exitosamente"
        )
        
    except GroupAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except TeacherNotFoundException as e:
        return not_found_response("Profesor", group_data.id_docente)
    except ValidationException as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error inesperado creando grupo: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{group_code}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar grupo",
    description=("**Disponible para:** Solo Administradores.\n\n"
        "Actualiza la información de un grupo existente"),
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_group(
    request: Request,
    group_code: str,
    group_data: GroupUpdate,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Solo administradores pueden actualizar grupos
    """
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
    except TeacherNotFoundException as e:
        return not_found_response("Profesor", group_data.id_docente if group_data.id_docente else "no especificado")
    except ValidationException as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando grupo {group_code}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/sin-materia/asignados",
    status_code=status.HTTP_200_OK,
    summary="Obtener grupos sin materia asignada",
    description=("**Disponible para:** Solo Administradores.\n\n"
        "Obtiene todos los grupos que no tienen materia asignada"),
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_groups_without_subject(
    request: Request,
    current_admin: Dict[str, Any] = Depends(require_admin) 
):
    """
    Solo administradores pueden ver grupos sin materia asignada (información interna)
    """
    try:
        service = GroupService()
        groups = await service.get_groups_without_subject()
        
        return success_response(
            data=[group.model_dump() for group in groups],
            message="Grupos sin materia asignada obtenidos correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo grupos sin materia: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{group_code}/desactivar",
    status_code=status.HTTP_200_OK,
    summary="Desactivar grupo",
    description=("**Disponible para:** Solo Administradores.\n\n"
        "Desactiva un grupo de forma lógica (no elimina el registro)"),
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def deactivate_group(
    request: Request,
    group_code: str,
    razon: ReasonText = Body(..., embed=True),
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Solo administradores pueden desactivar grupos
    """
    try:
        service = GroupService()
        success = await service.deactivate_group(group_code, razon)
        
        if success:
            logger.info(f"Grupo desactivado: {group_code} por {current_admin['nombre_completo']}")
            return message_response("Grupo desactivado exitosamente")
        else:
            return bad_request_response(message="No se pudo desactivar el grupo")
            
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except GroupHasDependenciesException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error desactivando grupo {group_code}: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{group_code}/activar",
    status_code=status.HTTP_200_OK,
    summary="Activar grupo",
    description=("**Disponible para:** Solo Administradores.\n\n"
        "Activa un grupo previamente desactivado"),
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def activate_group(
    request: Request,
    group_code: str,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Solo administradores pueden activar grupos
    """
    try:
        service = GroupService()
        success = await service.activate_group(group_code)
        
        if success:
            logger.info(f"Grupo activado: {group_code} por {current_admin['nombre_completo']}")
            return message_response("Grupo activado exitosamente")
        else:
            return bad_request_response(message="No se pudo activar el grupo")
            
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except Exception as e:
        logger.error(f"Error activando grupo {group_code}: {str(e)}")
        return internal_server_error_response()