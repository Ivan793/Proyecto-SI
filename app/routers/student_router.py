from fastapi import APIRouter, Body, Depends, Request, status
from typing import Dict, Any
import logging

from app.dependencies.service_dependencies import get_student_service
from app.exceptions.base_exceptions import DatabaseException, ValidationException
from app.schemas.types import ReasonText
from app.services.student_service import StudentService
from app.schemas.student import (
    StudentCreateWithUser, 
    StudentProfileUpdate,
)
from app.dependencies.auth_dependencies import get_current_student_user, require_student
from app.core.rate_limiter import auth_rate_limit
from app.utils.responses import (
    success_response, 
    created_response, 
    updated_response, 
)
from app.exceptions.student_exceptions import StudentNotFoundException


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])



# Registro público de estudiante
@router.post(
    "/registro",
    status_code=status.HTTP_201_CREATED,
    summary="Registro de estudiante",
    description="""Registro público de estudiante con creación de usuario asociado 
    (incluye datos personales, académicos y periodo actual)."""
)
@auth_rate_limit()
async def register_student(
    request: Request,
    student_data: StudentCreateWithUser = Body(...),
    service: StudentService = Depends(get_student_service)
):
    """
    Registra un nuevo estudiante con su usuario asociado.
    
    - **Transacción atómica**: Si falla algún paso, se revierte todo
    - **Validaciones**: Email institucional, programa existe, semestre válido, contraseña segura
    - **Email de verificación**: Se envía automáticamente
    - **Rate limiting**: Protección contra abuso
    """
    # LAS EXCEPCIONES SE PROPAGAN AL MANEJADOR GLOBAL
    student = await service.create_student_with_user(student_data)

    logger.info(f"Estudiante registrado correctamente: {student.id_estudiante}")

    return created_response(
        data=student.model_dump(),
        message="Estudiante registrado exitosamente"
    )


@router.get(
    "/mi-perfil",
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil del estudiante actual",
    description="""Obtiene el perfil completo del estudiante autenticado (datos estudiante + usuario).""",
)
async def get_my_profile(
    request: Request,
    current_student: Dict[str, Any] = Depends(require_student),
    service: StudentService = Depends(get_student_service) 
):
    """
    Obtiene el perfil completo del estudiante autenticado.
    
    - **Requiere autenticación**: Token JWT válido
    - **Información completa**: Datos de estudiante y usuario
    """
    # LAS EXCEPCIONES SE PROPAGAN AL MANEJADOR GLOBAL
    
    # Obtener estudiante por user_id del token
    student = await service.student_repo.get_student_by_user_id(
        current_student["user_id"]
    )
    
    # Obtener perfil completo
    student_with_user = await service.get_student_with_user(
        student["id_estudiante"]
    )
    
    return success_response(
        data=student_with_user.model_dump(),
        message="Perfil obtenido correctamente"
    )



# Actualizar perfil del estudiante autenticado
@router.put(
    "/mi-perfil",
    status_code=status.HTTP_200_OK,
    summary="Actualizar perfil del estudiante actual",
    description="""Actualiza el perfil completo del estudiante autenticado (datos estudiante + usuario).""",
)
async def update_my_profile(
    request: Request,
    student_data: StudentProfileUpdate,
    current_student: Dict[str, Any] = Depends(require_student),
    service: StudentService = Depends(get_student_service)
):
    """
    Actualiza el perfil completo del estudiante autenticado.
    
    - **Requiere autenticación**: Token JWT válido con rol Estudiante
    - **Transacción atómica**: Estudiante y usuario se actualizan juntos en Firestore
    - **Contraseña**: Se actualiza en Firebase Auth (operación separada)
    - **Campos opcionales**: Solo se actualizan los campos proporcionados
    - **Validaciones**: Semestre válido, coherencia con año de ingreso, etc.
    """
    # LAS EXCEPCIONES SE PROPAGAN AL MANEJADOR GLOBAL
    
    # Obtener estudiante por user_id del token
    student = await service.student_repo.get_student_by_user_id(
        current_student["user_id"]
    )
    
    # Actualizar perfil con transacción atómica
    updated_profile = await service.update_student(
        student["id_estudiante"], 
        student_data
    )
    
    logger.info(
        f"Perfil actualizado exitosamente: {student['id_estudiante']}",
        extra={"user_id": current_student["user_id"]}
    )
    
    return updated_response(
        data=updated_profile.model_dump(),
        message="Perfil actualizado exitosamente"
    )
