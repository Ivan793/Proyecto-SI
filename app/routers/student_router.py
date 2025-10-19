from fastapi import APIRouter, Body, Depends, Request, status
from typing import Dict, Any
import logging

from app.schemas.types import ReasonText
from app.services.student_service import StudentService
from app.schemas.student import StudentUpdate, StudentResponse
from app.dependencies.auth_dependencies import get_current_student_user
from app.core.rate_limiter import auth_rate_limit
from app.utils.responses import (
    success_response, created_response, updated_response, 
    not_found_response, bad_request_response, internal_server_error_response
)
from app.exceptions.student_exceptions import StudentNotFoundException
from app.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])

@router.post(
    "/registro",
    status_code=status.HTTP_201_CREATED,
    summary="Registro de estudiante",
    description="""Registro público de estudiante con creación de usuario."""
)
@auth_rate_limit()
async def register_student(
    request: Request,
    student_data: dict  # Cambiado a dict para flexibilidad en el registro
):
    """
    Endpoint público para que los estudiantes se registren automáticamente.
    No requiere autenticación previa.
    """
    try:
        service = StudentService()
        
        # Convertir el dict al schema apropiado
        from app.schemas.student import StudentCreateWithUser
        student_create_data = StudentCreateWithUser(**student_data)
        
        student = await service.create_student_with_user(student_create_data)
        
        logger.info(f"Estudiante registrado: {student.id_estudiante}")
        
        return created_response(
            data=student.model_dump(),
            message="Estudiante registrado exitosamente"
        )
        
    except UserAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error registrando estudiante: {str(e)}")
        return internal_server_error_response()

@router.get(
    "/mi-perfil",
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil del estudiante actual"
)
async def get_my_profile(
    request: Request,
    current_student: Dict[str, Any] = Depends(get_current_student_user)
):
    """
    El estudiante autenticado puede ver su propio perfil completo
    """
    try:
        service = StudentService()
        
        # Buscar el estudiante por ID de usuario
        student = await service.student_repo.get_student_by_user_id(current_student["user_id"])
        if not student:
            return not_found_response("Estudiante", "asociado a su usuario")
        
        # Obtener información completa del estudiante
        student_with_user = await service.get_student_with_user(student["id_estudiante"])
        
        return success_response(
            data=student_with_user.model_dump(),
            message="Perfil obtenido correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo perfil: {str(e)}")
        return internal_server_error_response()

@router.put(
    "/mi-perfil",
    status_code=status.HTTP_200_OK,
    summary="Actualizar perfil del estudiante actual"
)
async def update_my_profile(
    request: Request,
    student_data: StudentUpdate,
    current_student: Dict[str, Any] = Depends(get_current_student_user)
):
    """
    El estudiante autenticado puede actualizar ciertos campos de su perfil
    """
    try:
        service = StudentService()
        
        # Buscar el estudiante por ID de usuario
        student = await service.student_repo.get_student_by_user_id(current_student["user_id"])
        if not student:
            return not_found_response("Estudiante", "asociado a su usuario")
        
        # Actualizar solo campos permitidos para el estudiante
        allowed_fields = {"semestre", "codigo_programa"}  # Campos que el estudiante puede modificar
        update_data = {k: v for k, v in student_data.model_dump(exclude_none=True).items() 
                    if k in allowed_fields}
        
        if update_data:
            updated_student = await service.update_student(student["id_estudiante"], 
            StudentUpdate(**update_data))
            return updated_response(
                data=updated_student.model_dump(),
                message="Perfil actualizado exitosamente"
            )
        else:
            return bad_request_response(message="No hay campos válidos para actualizar")
        
    except StudentNotFoundException:
        return not_found_response("Estudiante", "asociado a su usuario")
    except Exception as e:
        logger.error(f"Error actualizando perfil: {str(e)}")
        return internal_server_error_response()

# Importar aquí para evitar dependencias circulares
from app.utils.responses import conflict_response