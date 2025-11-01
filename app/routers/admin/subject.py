from fastapi import APIRouter, Body, Depends, Query, status, Request
from typing import Optional, Dict, Any, List
import logging

from pydantic import BaseModel

from app.schemas.types import ReasonText
from app.services.subject_service import SubjectService
from app.schemas.subject import (
    SubjectCreate, 
    SubjectWithGroupsCreate, 
    SubjectUpdate, 
    SubjectResponse
)
from app.schemas.common import PaginationParams
from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response,
    message_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.subject_exceptions import (
    SubjectNotFoundException, 
    SubjectAlreadyExistsException,
    SubjectHasDependenciesException,
    MinimumGroupsRequiredException
)
from app.exceptions.group_exceptions import GroupNotFoundException
from app.exceptions.base_exceptions import ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Materias - Admin"])



@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva materia simple",
    description="Crea una nueva materia sin grupos asignados",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_subject_simple(
    request: Request,
    subject_data: SubjectCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        subject = await service.create_subject_simple(subject_data, current_admin["user_id"])
        
        logger.info(f"Materia creada: {subject.codigo_materia} por {current_admin['nombre_completo']}")
        
        return created_response(
            data=subject.model_dump(),
            message="Materia creada exitosamente"
        )
        
    except SubjectAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error inesperado creando materia: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.post(
    "/con-grupos",
    status_code=status.HTTP_201_CREATED,
    summary="Crear materia con grupos existentes",
    description="Crea una nueva materia y asigna grupos existentes a ella",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_subject_with_groups(
    request: Request,
    subject_with_groups: SubjectWithGroupsCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        subject = await service.create_subject_with_groups(subject_with_groups, current_admin["user_id"])
        
        logger.info(
            f"Materia creada con grupos: {subject.codigo_materia} con "
            f"{len(subject_with_groups.codigos_grupo)} grupos por {current_admin['nombre_completo']}"
        )
        
        return created_response(
            data=subject.model_dump(),
            message=f"Materia creada exitosamente con {len(subject_with_groups.codigos_grupo)} grupos asignados"
        )
        
    except SubjectAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except MinimumGroupsRequiredException as e:
        return bad_request_response(message=str(e))
    except GroupNotFoundException as e:
        return not_found_response("Grupo", str(e.identifier) if hasattr(e, 'identifier') else "no especificado")
    except Exception as e:
        logger.error(f"Error inesperado creando materia con grupos: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar todas las materias",
    description="Obtiene la lista de materias con opciones de filtrado y paginación",
    responses=ResponseDocumentation.get_paginated_response()
)
@admin_rate_limit()
async def get_subjects(
    request: Request,
    activos: bool = Query(True, description="Filtrar solo materias activas"),
    params: PaginationParams = Depends(),
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        subjects, total = await service.get_all_subjects(
            active_only=activos,
            page=params.page,
            limit=params.limit
        )

        return paginated_response(
            data=[subject.model_dump() for subject in subjects],
            page=params.page,
            limit=params.limit,
            total_items=total,
            message="Materias obtenidas exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo materias: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{subject_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener materia por código",
    description="Obtiene información básica de una materia específica",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_subject_by_code(
    request: Request,
    subject_code: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        subject = await service.get_subject(subject_code)
        
        return success_response(
            data=subject.model_dump(),
            message="Materia obtenida correctamente"
        )
        
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except Exception as e:
        logger.error(f"Error obteniendo materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{subject_code}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener materia con grupos y docentes",
    description="Obtiene información completa de una materia incluyendo sus grupos y docentes asignados",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_subject_with_groups(
    request: Request,
    subject_code: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        subject_with_details = await service.get_subject_with_groups(subject_code)
        
        return success_response(
            data=subject_with_details,
            message="Materia con detalles completos obtenida correctamente"
        )
        
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except Exception as e:
        logger.error(f"Error obteniendo materia completa {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{subject_code}/docentes",
    status_code=status.HTTP_200_OK,
    summary="Obtener docentes de la materia",
    description="Obtiene todos los docentes asignados a una materia específica",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_teachers_for_subject(
    request: Request,
    subject_code: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        teachers = await service.get_teachers_for_subject(subject_code)
        
        return success_response(
            data=teachers,
            message=f"Docentes de la materia {subject_code} obtenidos correctamente"
        )
        
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except Exception as e:
        logger.error(f"Error obteniendo docentes de materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{subject_code}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar materia",
    description="Actualiza la información de una materia existente",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_subject(
    request: Request,
    subject_code: str,
    subject_data: SubjectUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        subject = await service.update_subject(subject_code, subject_data)
        
        logger.info(f"Materia actualizada: {subject_code} por {current_admin['nombre_completo']}")
        
        return updated_response(
            data=subject.model_dump(),
            message="Materia actualizada exitosamente"
        )
        
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except Exception as e:
        logger.error(f"Error actualizando materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.post(
    "/{subject_code}/grupos/{group_code}",
    status_code=status.HTTP_200_OK,
    summary="Agregar grupo a materia",
    description="Agrega un grupo existente a una materia",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def add_group_to_subject(
    request: Request,
    subject_code: str,
    group_code: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        success = await service.add_group_to_subject(subject_code, group_code)
        
        if success:
            logger.info(f"Grupo {group_code} agregado a materia {subject_code} por {current_admin['nombre_completo']}")
            return message_response("Grupo agregado a la materia exitosamente")
        else:
            return bad_request_response(
                message="No se pudo agregar el grupo a la materia"
            )
            
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except ValidationException as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error agregando grupo a materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.post(
    "/{subject_code}/grupos-multiples",
    status_code=status.HTTP_200_OK,
    summary="Agregar múltiples grupos a materia",
    description="Agrega varios grupos existentes a una materia",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def add_groups_to_subject(
    request: Request,
    subject_code: str,
    codigos_grupo: List[str] = Body(..., embed=True, description="Lista de códigos de grupos"),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        result = await service.add_groups_to_subject(subject_code, codigos_grupo)
        
        logger.info(f"{len(codigos_grupo)} grupos agregados a materia {subject_code} por {current_admin['nombre_completo']}")
        
        return success_response(
            data=result,
            message=f"{len(codigos_grupo)} grupos agregados a la materia exitosamente"
        )
            
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except GroupNotFoundException as e:
        return not_found_response("Grupo", str(e.identifier) if hasattr(e, 'identifier') else "no especificado")
    except Exception as e:
        logger.error(f"Error agregando grupos a materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.delete(
    "/{subject_code}/grupos/{group_code}",
    status_code=status.HTTP_200_OK,
    summary="Remover grupo de materia",
    description="Remueve un grupo de una materia",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def remove_group_from_subject(
    request: Request,
    subject_code: str,
    group_code: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        success = await service.remove_group_from_subject(subject_code, group_code)
        
        if success:
            logger.info(f"Grupo {group_code} removido de materia {subject_code} por {current_admin['nombre_completo']}")
            return message_response("Grupo removido de la materia exitosamente")
        else:
            return bad_request_response(
                message="No se pudo remover el grupo de la materia"
            )
            
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except GroupNotFoundException as e:
        return not_found_response("Grupo", group_code)
    except Exception as e:
        logger.error(f"Error removiendo grupo de materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{subject_code}/desactivar",
    status_code=status.HTTP_200_OK,
    summary="Desactivar materia",
    description="Desactiva una materia de forma lógica (no elimina el registro)",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def deactivate_subject(
    request: Request,
    subject_code: str,
    razon: ReasonText = Body(..., embed=True),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        success = await service.deactivate_subject(subject_code, razon)
        
        if success:
            logger.info(f"Materia desactivada: {subject_code} por {current_admin['nombre_completo']}")
            return message_response("Materia desactivada exitosamente")
        else:
            return bad_request_response(
                message="No se pudo desactivar la materia"
            )
            
    except SubjectNotFoundException as e:
        return not_found_response("Materia", subject_code)
    except SubjectHasDependenciesException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error desactivando materia {subject_code}: {str(e)}")
        return internal_server_error_response()
    

@router.patch(
    "/{subject_code}/activar",
    status_code=status.HTTP_200_OK,
    summary="Activar Materia",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def activate_subject(
    request: Request,
    subject_code: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubjectService()
        success = await service.activate_subject(subject_code)
        
        if success:
            logger.info(f"Materia activada: {subject_code}")
            return message_response("Materia activada exitosamente")
        return bad_request_response(message="No se pudo activar la materia")
            
    except SubjectNotFoundException:
        return not_found_response("Materia", subject_code)
    except Exception as e:
        logger.error(f"Error activando materia {subject_code}: {str(e)}")
        return internal_server_error_response()