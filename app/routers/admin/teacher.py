from fastapi import APIRouter, Body, Depends, Query, status, Request
from typing import Optional, Dict, Any
import logging

from app.schemas.types import ReasonText
from app.services.teacher_service import TeacherService
from app.schemas.teacher import (
    TeacherCreateWithUser,
    TeacherCreateWithExistingUser, 
    TeacherUpdate, 
    TeacherResponse
)
from app.schemas.common import PaginationParams
from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response
)
from app.exceptions.teacher_exceptions import (
    TeacherNotFoundException, 
    TeacherAlreadyExistsException, 
    TeacherHasAssignmentsException
)
from app.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Profesores - Admin"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear profesor con usuario (CASCADA)",
    description=""" Crea un profesor Y su usuario asociado en una sola operación."""
)
@admin_rate_limit()
async def create_teacher_with_user(
    request: Request,
    teacher_data: TeacherCreateWithUser,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherService()
        teacher = await service.create_teacher_with_user(teacher_data)
        
        logger.info(
            f"Profesor + Usuario creados en cascada por {current_admin['nombre_completo']}"
        )
        
        return created_response(
            data=teacher.model_dump(),
            message="Profesor y usuario creados exitosamente"
        )
        
    except UserAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando profesor con usuario: {str(e)}")
        return internal_server_error_response()

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar todos los profesores"
)
@admin_rate_limit()
async def get_teachers(
    request: Request,
    activos: bool = Query(True, description="Filtrar solo profesores activos"),
    params: PaginationParams = Depends(),
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherService()
        teachers, total = await service.get_all_teachers(
            active_only=activos,
            page=params.page,
            limit=params.limit
        )

        return paginated_response(
            data=[teacher.model_dump() for teacher in teachers],
            page=params.page,
            limit=params.limit,
            total_items=total
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo profesores: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{teacher_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener profesor por ID"
)
@admin_rate_limit()
async def get_teacher_by_id(
    request: Request,
    teacher_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherService()
        teacher = await service.get_teacher(teacher_id)
        
        return success_response(
            data=teacher.model_dump(),
            message="Profesor obtenido correctamente"
        )
        
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except Exception as e:
        logger.error(f"Error obteniendo profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{teacher_id}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener profesor con información de usuario"
)
@admin_rate_limit()
async def get_teacher_with_user(
    request: Request,
    teacher_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherService()
        teacher_with_user = await service.get_teacher_with_user(teacher_id)
        
        return success_response(
            data=teacher_with_user.model_dump(),
            message="Profesor con información completa"
        )
        
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except UserNotFoundException:
        return not_found_response("Usuario", "asociado al profesor")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{teacher_id}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar profesor"
)
@admin_rate_limit()
async def update_teacher(
    request: Request,
    teacher_id: str,
    teacher_data: TeacherUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherService()
        teacher = await service.update_teacher(teacher_id, teacher_data)
        
        logger.info(f"Profesor actualizado: {teacher_id} por {current_admin['nombre_completo']}")
        
        return updated_response(
            data=teacher.model_dump(),
            message="Profesor actualizado exitosamente"
        )
        
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except Exception as e:
        logger.error(f"Error actualizando profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{teacher_id}/desactivar",
    status_code=status.HTTP_200_OK,
    summary="Desactivar profesor"
)
@admin_rate_limit()
async def deactivate_teacher(
    request: Request,
    teacher_id: str,
    razon: ReasonText = Body(..., embed=True),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherService()
        success = await service.deactivate_teacher(teacher_id, razon)
        
        if success:
            logger.info(f"Profesor desactivado: {teacher_id}")
            return success_response(
                data={"desactivado": True},
                message="Profesor desactivado exitosamente"
            )
        return bad_request_response(message="No se pudo desactivar")
            
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except TeacherHasAssignmentsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{teacher_id}/activar",
    status_code=status.HTTP_200_OK,
    summary="Activar profesor"
)
@admin_rate_limit()
async def activate_teacher(
    request: Request,
    teacher_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherService()
        success = await service.activate_teacher(teacher_id)
        
        if success:
            logger.info(f"Profesor activado: {teacher_id}")
            return success_response(
                data={"activado": True},
                message="Profesor activado exitosamente"
            )
        return bad_request_response(message="No se pudo activar")
            
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return internal_server_error_response()