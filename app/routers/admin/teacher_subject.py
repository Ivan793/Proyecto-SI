# app/routers/admin/teacher_subject.py
from fastapi import APIRouter, Body, Depends, Query, status, Request
from typing import Optional, Dict, Any, List
import logging

from app.schemas.types import ReasonText
from app.services.teacher_subject_service import TeacherSubjectService
from app.schemas.teacherSubject import TeacherSubjectCreate, TeacherSubjectUpdate, TeacherSubjectResponse
from app.schemas.common import PaginationParams
from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response
)
from app.exceptions.teacher_subject_exceptions import (
    TeacherSubjectNotFoundException,
    TeacherSubjectAlreadyExistsException,
    TeacherSubjectAssignmentException
)
from app.exceptions.teacher_exceptions import TeacherNotFoundException
from app.exceptions.subject_exceptions import SubjectNotFoundException
from app.exceptions.group_exceptions import GroupNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Asignaciones Docente-Materia - Admin"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear asignación docente-materia",
    description="Asigna un docente a una materia y grupo específico"
)
@admin_rate_limit()
async def create_teacher_subject_assignment(
    request: Request,
    assignment_data: TeacherSubjectCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        assignment = await service.create_assignment(
            assignment_data, 
            current_admin["user_id"]
        )
        
        logger.info(
            f"Asignación creada: docente {assignment_data.id_docente} -> "
            f"materia {assignment_data.codigo_materia} grupo {assignment_data.codigo_grupo} "
            f"por {current_admin['nombre_completo']}"
        )
        
        return created_response(
            data=assignment.model_dump(),
            message="Asignación docente-materia creada exitosamente"
        )
        
    except TeacherSubjectAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except TeacherNotFoundException as e:
        return not_found_response("Profesor", assignment_data.id_docente)
    except SubjectNotFoundException as e:
        return not_found_response("Materia", assignment_data.codigo_materia)
    except GroupNotFoundException as e:
        return not_found_response("Grupo", assignment_data.codigo_grupo)
    except TeacherSubjectAssignmentException as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando asignación docente-materia: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{assignment_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener asignación por ID"
)
@admin_rate_limit()
async def get_assignment_by_id(
    request: Request,
    assignment_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        assignment = await service.get_assignment(assignment_id)
        
        return success_response(
            data=assignment.model_dump(),
            message="Asignación obtenida correctamente"
        )
        
    except TeacherSubjectNotFoundException:
        return not_found_response("Asignación docente-materia", assignment_id)
    except Exception as e:
        logger.error(f"Error obteniendo asignación {assignment_id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/docente/{teacher_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener asignaciones por docente"
)
@admin_rate_limit()
async def get_assignments_by_teacher(
    request: Request,
    teacher_id: str,
    activos: bool = Query(True, description="Filtrar solo asignaciones activas"),
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        assignments = await service.get_assignments_by_teacher(teacher_id, activos)
        
        return success_response(
            data=[assignment.model_dump() for assignment in assignments],
            message=f"Asignaciones del docente {teacher_id} obtenidas correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo asignaciones del docente {teacher_id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/materia/{subject_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener asignaciones por materia"
)
@admin_rate_limit()
async def get_assignments_by_subject(
    request: Request,
    subject_code: str,
    activos: bool = Query(True, description="Filtrar solo asignaciones activas"),
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        assignments = await service.get_assignments_by_subject(subject_code, activos)
        
        return success_response(
            data=[assignment.model_dump() for assignment in assignments],
            message=f"Asignaciones de la materia {subject_code} obtenidas correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo asignaciones de la materia {subject_code}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/grupo/{group_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener asignaciones por grupo"
)
@admin_rate_limit()
async def get_assignments_by_group(
    request: Request,
    group_code: int,
    activos: bool = Query(True, description="Filtrar solo asignaciones activas"),
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        assignments = await service.get_assignments_by_group(group_code, activos)
        
        return success_response(
            data=[assignment.model_dump() for assignment in assignments],
            message=f"Asignaciones del grupo {group_code} obtenidas correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo asignaciones del grupo {group_code}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{assignment_id}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar asignación"
)
@admin_rate_limit()
async def update_assignment(
    request: Request,
    assignment_id: str,
    assignment_data: TeacherSubjectUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        assignment = await service.update_assignment(assignment_id, assignment_data)
        
        logger.info(f"Asignación actualizada: {assignment_id} por {current_admin['nombre_completo']}")
        
        return updated_response(
            data=assignment.model_dump(),
            message="Asignación actualizada exitosamente"
        )
        
    except TeacherSubjectNotFoundException:
        return not_found_response("Asignación docente-materia", assignment_id)
    except TeacherNotFoundException as e:
        return not_found_response("Profesor", assignment_data.id_docente)
    except SubjectNotFoundException as e:
        return not_found_response("Materia", assignment_data.codigo_materia)
    except GroupNotFoundException as e:
        return not_found_response("Grupo", assignment_data.codigo_grupo)
    except TeacherSubjectAssignmentException as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando asignación {assignment_id}: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{assignment_id}/desactivar",
    status_code=status.HTTP_200_OK,
    summary="Desactivar asignación"
)
@admin_rate_limit()
async def deactivate_assignment(
    request: Request,
    assignment_id: str,
    razon: ReasonText = Body(..., embed=True),
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        success = await service.deactivate_assignment(assignment_id, razon)
        
        if success:
            logger.info(f"Asignación desactivada: {assignment_id} por {current_admin['nombre_completo']}")
            return success_response(
                data={"desactivado": True},
                message="Asignación desactivada exitosamente"
            )
        return bad_request_response(message="No se pudo desactivar la asignación")
            
    except TeacherSubjectNotFoundException:
        return not_found_response("Asignación docente-materia", assignment_id)
    except Exception as e:
        logger.error(f"Error desactivando asignación {assignment_id}: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{assignment_id}/activar",
    status_code=status.HTTP_200_OK,
    summary="Activar asignación"
)
@admin_rate_limit()
async def activate_assignment(
    request: Request,
    assignment_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        success = await service.activate_assignment(assignment_id)
        
        if success:
            logger.info(f"Asignación activada: {assignment_id} por {current_admin['nombre_completo']}")
            return success_response(
                data={"activado": True},
                message="Asignación activada exitosamente"
            )
        return bad_request_response(message="No se pudo activar la asignación")
            
    except TeacherSubjectNotFoundException:
        return not_found_response("Asignación docente-materia", assignment_id)
    except Exception as e:
        logger.error(f"Error activando asignación {assignment_id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/docente/{teacher_id}/carga",
    status_code=status.HTTP_200_OK,
    summary="Obtener carga de trabajo del docente"
)
@admin_rate_limit()
async def get_teacher_workload(
    request: Request,
    teacher_id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = TeacherSubjectService()
        workload = await service.get_teacher_workload(teacher_id)
        
        return success_response(
            data=workload,
            message="Carga de trabajo obtenida correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo carga de trabajo del docente {teacher_id}: {str(e)}")
        return internal_server_error_response()