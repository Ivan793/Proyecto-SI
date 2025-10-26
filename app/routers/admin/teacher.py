# app/routers/teacher_router.py
from fastapi import APIRouter, Body, Depends, Query, status, Request
from typing import Dict, Any
import logging

from app.schemas.types import ReasonText
from app.services.teacher_service import TeacherService
from app.schemas.teacher import (
    TeacherCreateWithUser,
    TeacherUpdate, 
    TeacherResponse
)
from app.schemas.common import PaginationParams
from app.dependencies.auth_dependencies import get_current_admin_user
from app.dependencies.service_dependencies import get_teacher_service
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, message_response
)
from app.utils.swagger_docs import ResponseDocumentation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Profesores - Admin"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear profesor con usuario (CASCADA)",
    description="Crea un profesor Y su usuario asociado en una sola operación.",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_teacher_with_user(
    request: Request,
    teacher_data: TeacherCreateWithUser,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    teacher = await service.create_teacher_with_user(teacher_data)
    
    logger.info(
        f"Profesor + Usuario creados en cascada por {current_admin['nombre_completo']}"
    )
    
    return created_response(
        data=teacher.model_dump(),
        message="Profesor y usuario creados exitosamente"
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar todos los profesores",
    responses=ResponseDocumentation.get_paginated_response()
)
@admin_rate_limit()
async def get_teachers(
    request: Request,
    activos: bool = Query(True, description="Filtrar solo profesores activos"),
    params: PaginationParams = Depends(),
    _: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    teachers, total = await service.get_all_teachers(
        active_only=activos,
        page=params.page,
        limit=params.limit
    )

    return paginated_response(
        data=[teacher.model_dump() for teacher in teachers],
        page=params.page,
        limit=params.limit,
        total_items=total,
        message="Profesores obtenidos exitosamente"
    )


@router.get(
    "/{teacher_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener profesor por ID",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_teacher_by_id(
    request: Request,
    teacher_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    teacher = await service.get_teacher(teacher_id)
    
    return success_response(
        data=teacher.model_dump(),
        message="Profesor obtenido correctamente"
    )


@router.get(
    "/{teacher_id}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener profesor con información de usuario",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_teacher_with_user(
    request: Request,
    teacher_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    teacher_with_user = await service.get_teacher_with_user(teacher_id)
    
    return success_response(
        data=teacher_with_user.model_dump(),
        message="Profesor con información completa"
    )


@router.put(
    "/{teacher_id}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar profesor",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_teacher(
    request: Request,
    teacher_id: str,
    teacher_data: TeacherUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    teacher = await service.update_teacher(teacher_id, teacher_data)
    
    logger.info(f"Profesor actualizado: {teacher_id} por {current_admin['nombre_completo']}")
    
    return updated_response(
        data=teacher.model_dump(),
        message="Profesor actualizado exitosamente"
    )


@router.patch(
    "/{teacher_id}/desactivar",
    status_code=status.HTTP_200_OK,
    summary="Desactivar profesor",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def deactivate_teacher(
    request: Request,
    teacher_id: str,
    razon: ReasonText = Body(..., embed=True),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    success = await service.deactivate_teacher(teacher_id, razon)
    
    if success:
        logger.info(f"Profesor desactivado: {teacher_id}")
        return message_response("Profesor desactivado exitosamente")
    
    return message_response("No se pudo desactivar el profesor", status_code=400)


@router.patch(
    "/{teacher_id}/activar",
    status_code=status.HTTP_200_OK,
    summary="Activar profesor",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def activate_teacher(
    request: Request,
    teacher_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    success = await service.activate_teacher(teacher_id)
    
    if success:
        logger.info(f"Profesor activado: {teacher_id}")
        return message_response("Profesor activado exitosamente")
    
    return message_response("No se pudo activar el profesor", status_code=400)


@router.get(
    "/programa/{program_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener profesores por programa",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_teachers_by_program(
    request: Request,
    program_code: str,
    _: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    teachers = await service.get_teachers_by_program(program_code)
    
    return success_response(
        data=[teacher.model_dump() for teacher in teachers],
        message=f"Profesores del programa {program_code} obtenidos correctamente"
    )


@router.get(
    "/{teacher_id}/carga",
    status_code=status.HTTP_200_OK,
    summary="Obtener carga de trabajo del profesor",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_teacher_workload(
    request: Request,
    teacher_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user),
    service: TeacherService = Depends(get_teacher_service)
):
    workload = await service.get_teacher_workload(teacher_id)
    
    return success_response(
        data=workload,
        message="Carga de trabajo obtenida correctamente"
    )