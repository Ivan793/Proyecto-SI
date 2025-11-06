from fastapi import APIRouter, Body, Depends, Query, status, Request
from typing import Optional, Dict, Any
import logging

from app.schemas.types import ReasonText
from app.services.student_service import StudentService
from app.schemas.student import (
    StudentCreateWithUser,
    StudentUpdate, 
    StudentResponse
)
from app.schemas.common import PaginationParams
from app.dependencies.auth_dependencies import (
    get_current_admin_user, 
    require_admin_or_teacher, 
    require_admin_teacher_or_student
)
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response
)
from app.exceptions.student_exceptions import (
    StudentNotFoundException, 
    StudentAlreadyExistsException
)
from app.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Estudiantes - Administración"])


# Crear estudiante con usuario existente
@router.post(
    "/asignar-existente",
    status_code=status.HTTP_201_CREATED,
    summary="Crear estudiante con usuario EXISTENTE",
    description="""Asigna un usuario que **ya existe en el sistema** como estudiante.  
    Este endpoint es de uso exclusivo para administradores."""
)
@admin_rate_limit()



# Listar estudiantes
@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar todos los estudiantes",
    description="Obtiene una lista paginada de estudiantes. Solo visible para administradores y profesores."
)
async def get_students(
    request: Request,
    activos: bool = Query(True, description="Filtrar solo estudiantes activos"),
    params: PaginationParams = Depends(),
    current_user: Dict[str, Any] = Depends(require_admin_teacher_or_student)
):
    try:
        service = StudentService()
        students, total = await service.get_all_students(
            active_only=activos,
            page=params.page,
            limit=params.limit
        )

        return paginated_response(
            data=[student.model_dump() for student in students],
            page=params.page,
            limit=params.limit,
            total_items=total
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estudiantes: {str(e)}")
        return internal_server_error_response()



# Obtener estudiante por ID
@router.get(
    "/{student_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiante por ID",
    description="Devuelve la información básica de un estudiante según su ID."
)
async def get_student_by_id(
    request: Request,
    student_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_or_teacher)
):
    try:
        service = StudentService()
        student = await service.get_student(student_id)
        
        return success_response(
            data=student.model_dump(),
            message="Estudiante obtenido correctamente"
        )
        
    except StudentNotFoundException:
        return not_found_response("Estudiante", student_id)
    except Exception as e:
        logger.error(f"❌ Error obteniendo estudiante {student_id}: {str(e)}")
        return internal_server_error_response()


# Obtener estudiante con datos del usuario
@router.get(
    "/{student_id}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiante con información de usuario",
    description="Solo administradores pueden ver la información completa del estudiante y su usuario asociado."
)
@admin_rate_limit()
async def get_student_with_user(
    request: Request,
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = StudentService()
        student_with_user = await service.get_student_with_user(student_id)
        
        return success_response(
            data=student_with_user.model_dump(),
            message="Estudiante con información completa"
        )
        
    except StudentNotFoundException:
        return not_found_response("Estudiante", student_id)
    except UserNotFoundException:
        return not_found_response("Usuario", "asociado al estudiante")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return internal_server_error_response()



# Actualizar estudiante
@router.put(
    "/{student_id}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar estudiante",
    description="Permite a los administradores modificar los datos académicos o el estado de un estudiante."
)
@admin_rate_limit()
async def update_student(
    request: Request,
    student_id: str,
    student_data: StudentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = StudentService()
        student = await service.update_student(student_id, student_data)
        
        logger.info(f"🛠️ Estudiante actualizado: {student_id} por {current_user['nombre_completo']}")
        
        return updated_response(
            data=student.model_dump(),
            message="Estudiante actualizado exitosamente"
        )
        
    except StudentNotFoundException:
        return not_found_response("Estudiante", student_id)
    except Exception as e:
        logger.error(f"❌ Error actualizando estudiante {student_id}: {str(e)}")
        return internal_server_error_response()



# Desactivar estudiante
@router.patch(
    "/{student_id}/desactivar",
    status_code=status.HTTP_200_OK,
    summary="Desactivar estudiante",
    description="Desactiva un estudiante del sistema. Solo administradores pueden realizar esta acción."
)
@admin_rate_limit()
async def deactivate_student(
    request: Request,
    student_id: str,
    razon: ReasonText = Body(..., embed=True),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = StudentService()
        success = await service.deactivate_student(student_id, razon)
        
        if success:
            logger.info(f"🧩 Estudiante desactivado: {student_id}")
            return success_response(
                data={"desactivado": True},
                message="Estudiante desactivado exitosamente"
            )
        return bad_request_response(message="No se pudo desactivar")
            
    except StudentNotFoundException:
        return not_found_response("Estudiante", student_id)
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return internal_server_error_response()


# Activar estudiante
@router.patch(
    "/{student_id}/activar",
    status_code=status.HTTP_200_OK,
    summary="Activar estudiante",
    description="Activa nuevamente un estudiante previamente desactivado."
)
@admin_rate_limit()
async def activate_student(
    request: Request,
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = StudentService()
        success = await service.activate_student(student_id)
        
        if success:
            logger.info(f"✅ Estudiante activado: {student_id}")
            return success_response(
                data={"activado": True},
                message="Estudiante activado exitosamente"
            )
        return bad_request_response(message="No se pudo activar")
            
    except StudentNotFoundException:
        return not_found_response("Estudiante", student_id)
    except Exception as e:
        logger.error(f" Error: {str(e)}")
        return internal_server_error_response()


# Obtener estudiantes por programa
@router.get(
    "/programa/{program_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes por programa",
    description="Filtra y devuelve todos los estudiantes asociados a un programa académico específico."
)
async def get_students_by_program(
    request: Request,
    program_code: str,
    current_user: Dict[str, Any] = Depends(require_admin_or_teacher)
):
    try:
        service = StudentService()
        students = await service.get_students_by_program(program_code)
        
        return success_response(
            data=[student.model_dump() for student in students],
            message=f"Estudiantes del programa {program_code}"
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estudiantes por programa: {str(e)}")
        return internal_server_error_response()
