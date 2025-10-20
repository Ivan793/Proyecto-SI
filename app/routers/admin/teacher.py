from fastapi import APIRouter, Body, Depends, Query, status, Request
from typing import Dict, Any
import logging

from app.schemas.teacher import (
    TeacherCreateWithUser,
    TeacherCreateWithExistingUser,
    TeacherUpdate
)
from app.schemas.common import PaginationParams
from app.services.teacher_service import TeacherService
from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response,
    created_response,
    paginated_response,
    updated_response,
    not_found_response,
    conflict_response,
    internal_server_error_response
)
from app.schemas.types import ReasonText
from app.exceptions.teacher_exceptions import (
    TeacherNotFoundException,
    TeacherAlreadyExistsException,
    TeacherHasAssignmentsException
)
from app.exceptions.user_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teachers", tags=["Profesores - Admin"])

service = TeacherService()

# ---------------------------
# Crear profesor con usuario en cascada
# ---------------------------
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear profesor con usuario (CASCADA)"
)
@admin_rate_limit()
async def create_teacher_with_user(
    request: Request,
    teacher_data: TeacherCreateWithUser,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        teacher = await service.create_teacher_with_user(teacher_data)
        logger.info(f"Profesor + Usuario creados por {current_admin['nombre_completo']}")
        return created_response(data=teacher.model_dump(), message="Profesor y usuario creados exitosamente")
    except UserAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando profesor con usuario: {str(e)}")
        return internal_server_error_response()

# ---------------------------
# Crear profesor asignando a usuario existente
# ---------------------------
@router.post(
    "/asignar-existente",
    status_code=status.HTTP_201_CREATED,
    summary="Asignar profesor a usuario existente"
)
@admin_rate_limit()
async def create_teacher_with_existing_user(
    request: Request,
    teacher_data: TeacherCreateWithExistingUser,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        teacher = await service.create_teacher_with_existing_user(teacher_data)
        logger.info(f"Profesor asignado a usuario existente por {current_admin['nombre_completo']}")
        return created_response(data=teacher.model_dump(), message="Profesor asignado correctamente")
    except TeacherAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except UserNotFoundException as e:
        return not_found_response("Usuario", teacher_data.id_usuario)
    except Exception as e:
        logger.error(f"Error asignando profesor a usuario existente: {str(e)}")
        return internal_server_error_response()

# ---------------------------
# Obtener todos los profesores (paginado)
# ---------------------------
@router.get(
    "",
    summary="Listar todos los profesores"
)
@admin_rate_limit()
async def get_all_teachers(
    request: Request,
    active_only: bool = Query(True, description="Solo profesores activos"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        teachers, total = await service.get_all_teachers(active_only=active_only, page=page, limit=limit)
        return paginated_response(
            data=[t.model_dump() for t in teachers],
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error obteniendo lista de profesores: {str(e)}")
        return internal_server_error_response()

# ---------------------------
# Obtener profesor por ID
# ---------------------------
@router.get(
    "/{teacher_id}",
    summary="Obtener profesor por ID"
)
@admin_rate_limit()
async def get_teacher(
    request: Request,
    teacher_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        teacher = await service.get_teacher(teacher_id)
        return success_response(data=teacher.model_dump())
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except Exception as e:
        logger.error(f"Error obteniendo profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()

# ---------------------------
# Obtener profesor con datos de usuario
# ---------------------------
@router.get(
    "/{teacher_id}/detalles",
    summary="Obtener profesor con datos del usuario"
)
@admin_rate_limit()
async def get_teacher_with_user(
    request: Request,
    teacher_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        teacher_with_user = await service.get_teacher_with_user(teacher_id)
        return success_response(data=teacher_with_user)
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except UserNotFoundException:
        return not_found_response("Usuario del profesor", teacher_id)
    except Exception as e:
        logger.error(f"Error obteniendo detalles del profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()

# ---------------------------
# Actualizar profesor
# ---------------------------
@router.put(
    "/{teacher_id}",
    summary="Actualizar datos del profesor"
)
@admin_rate_limit()
async def update_teacher(
    request: Request,
    teacher_id: str,
    teacher_data: TeacherUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        updated_teacher = await service.update_teacher(teacher_id, teacher_data)
        logger.info(f"Profesor {teacher_id} actualizado por {current_admin['nombre_completo']}")
        return updated_response(data=updated_teacher.model_dump())
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except Exception as e:
        logger.error(f"Error actualizando profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()

# ---------------------------
# Desactivar profesor
# ---------------------------
@router.patch(
    "/{teacher_id}/desactivar",
    summary="Desactivar profesor"
)
@admin_rate_limit()
async def deactivate_teacher(
    request: Request,
    teacher_id: str,
    reason: ReasonText = Body(..., description="Razón de desactivación"),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        await service.deactivate_teacher(teacher_id, reason.motivo)
        logger.info(f"Profesor {teacher_id} desactivado por {current_admin['nombre_completo']}")
        return updated_response(message="Profesor desactivado exitosamente")
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except TeacherHasAssignmentsException:
        return conflict_response(message="El profesor tiene asignaciones activas y no puede ser desactivado.")
    except Exception as e:
        logger.error(f"Error desactivando profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()

# ---------------------------
# Activar profesor
# ---------------------------
@router.patch(
    "/{teacher_id}/activar",
    summary="Reactivar profesor"
)
@admin_rate_limit()
async def activate_teacher(
    request: Request,
    teacher_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        await service.activate_teacher(teacher_id)
        logger.info(f"Profesor {teacher_id} reactivado por {current_admin['nombre_completo']}")
        return updated_response(message="Profesor reactivado exitosamente")
    except TeacherNotFoundException:
        return not_found_response("Profesor", teacher_id)
    except Exception as e:
        logger.error(f"Error reactivando profesor {teacher_id}: {str(e)}")
        return internal_server_error_response()
