from fastapi import APIRouter, Depends, Request, status, Path
from typing import Dict, Any
import logging

from app.exceptions.subject_exceptions import SubjectAlreadyExistsException, SubjectNotFoundException
from app.services.academic_service import AcademicService, FacultyService, ProgramService
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.schemas.program import ProgramCreate, ProgramUpdate

from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    created_response, updated_response, success_response,
    not_found_response, conflict_response, internal_server_error_response,
    bad_request_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.academic_exceptions import (
    FacultyNotFoundException, FacultyAlreadyExistsException,
    ProgramNotFoundException, ProgramAlreadyExistsException,
    InvalidFacultyException
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Académico - Admin"])

# ==================== FACULTADES ====================

@router.post(
    "/facultades",
    status_code=status.HTTP_201_CREATED,
    summary="Crear facultad",
    description="Solo Administradores. Crea una nueva facultad en el sistema",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_faculty(
    request: Request,
    faculty_data: FacultyCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = FacultyService()
        faculty = await service.create_faculty(faculty_data)
        
        logger.info(
            f"Facultad creada: {faculty.id_facultad} "
            f"por {current_user['nombre_completo']}"
        )
        
        return created_response(
            data=faculty.model_dump(),
            message="Facultad creada exitosamente"
        )
        
    except FacultyAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando facultad: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.get(
    "/facultades",
    status_code=status.HTTP_200_OK,
    summary="Listar todas las facultades",
    description="Solo Administradores. Obtiene la lista de todas las facultades",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_all_faculties(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = FacultyService()
        faculties = await service.get_all_faculties()
        
        return success_response(
            data=[faculty.model_dump() for faculty in faculties],
            message="Facultades obtenidas correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo facultades: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/facultades/{faculty_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener facultad por código",
    description="Solo Administradores. Obtiene información de una facultad específica",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_faculty(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = FacultyService()
        faculty = await service.get_faculty(faculty_id)
        
        return success_response(
            data=faculty.model_dump(),
            message="Facultad obtenida correctamente"
        )
        
    except FacultyNotFoundException:
        return not_found_response("Facultad", faculty_id)
    except Exception as e:
        logger.error(f"Error obteniendo facultad {faculty_id}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/facultades/{faculty_id}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar facultad",
    description="Solo Administradores. Actualiza información de una facultad",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_faculty(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    faculty_data: FacultyUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = FacultyService()
        faculty = await service.update_faculty(faculty_id, faculty_data)
        
        logger.info(
            f"Facultad actualizada: {faculty_id} "
            f"por {current_user['nombre_completo']}"
        )
        
        return updated_response(
            data=faculty.model_dump(),
            message="Facultad actualizada exitosamente"
        )
        
    except FacultyNotFoundException:
        return not_found_response("Facultad", faculty_id)
    except Exception as e:
        logger.error(f"Error actualizando facultad {faculty_id}: {str(e)}")
        return internal_server_error_response()


# ==================== PROGRAMAS ====================

@router.post(
    "/facultades/{faculty_id}/programas",
    status_code=status.HTTP_201_CREATED,
    summary="Crear programa académico",
    description="Solo Administradores. Crea un programa dentro de una facultad específica",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_program(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    program_data: ProgramCreate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        # Validar que el faculty_id del path coincida con el del body
        if program_data.id_facultad != faculty_id:
            return bad_request_response(
                message="El código de facultad en el path no coincide con el del cuerpo de la solicitud"
            )
        
        service = ProgramService()
        program = await service.create_program(program_data)
        
        logger.info(
            f"Programa creado: {program.codigo_programa} en facultad {faculty_id} "
            f"por {current_user['nombre_completo']}"
        )
        
        return created_response(
            data=program.model_dump(),
            message="Programa académico creado exitosamente"
        )
        
    except InvalidFacultyException as e:
        return not_found_response("Facultad", faculty_id)
    except ProgramAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando programa: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.get(
    "/facultades/{faculty_id}/programas",
    status_code=status.HTTP_200_OK,
    summary="Listar programas de una facultad",
    description="Solo Administradores. Obtiene todos los programas de una facultad",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_programs_by_faculty(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ProgramService()
        programs = await service.get_programs_by_faculty(faculty_id)
        
        return success_response(
            data=[program.model_dump() for program in programs],
            message="Programas obtenidos correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo programas de facultad {faculty_id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/facultades/{faculty_id}/programas/{program_code}",
    status_code=status.HTTP_200_OK,
    summary="Obtener programa específico",
    description="Solo Administradores. Obtiene información de un programa específico",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_program(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    program_code: str = Path(..., description="Código del programa"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ProgramService()
        program = await service.get_program(faculty_id, program_code)
        
        return success_response(
            data=program.model_dump(),
            message="Programa obtenido correctamente"
        )
        
    except ProgramNotFoundException:
        return not_found_response("Programa", program_code)
    except Exception as e:
        logger.error(f"Error obteniendo programa {program_code}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/facultades/{faculty_id}/programas/{program_code}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar programa",
    description="Solo Administradores. Actualiza información de un programa",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_program(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    program_code: str = Path(..., description="Código del programa"),
    program_data: ProgramUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ProgramService()
        program = await service.update_program(faculty_id, program_code, program_data)
        
        logger.info(
            f"Programa actualizado: {program_code} "
            f"por {current_user['nombre_completo']}"
        )
        
        return updated_response(
            data=program.model_dump(),
            message="Programa actualizado exitosamente"
        )
        
    except ProgramNotFoundException:
        return not_found_response("Programa", program_code)
    except ProgramAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando programa {program_code}: {str(e)}")
        return internal_server_error_response()
    

@router.post(
    "/facultades/{faculty_id}/programas/{program_code}/materias/{subject_code}",
    status_code=status.HTTP_200_OK,
    summary="Agregar materia a programa",
    description="Solo Administradores. Agrega una materia existente a un programa académico",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def add_subject_to_program(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    program_code: str = Path(..., description="Código del programa"),
    subject_code: str = Path(..., description="Código de la materia"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ProgramService()
        program = await service.add_subject_to_program(faculty_id, program_code, subject_code)
        
        logger.info(
            f"Materia {subject_code} agregada al programa {program_code} "
            f"por {current_user['nombre_completo']}"
        )
        
        return success_response(
            data=program.model_dump(),
            message="Materia agregada al programa exitosamente"
        )
        
    except (ProgramNotFoundException, SubjectNotFoundException) as e:
        return not_found_response(str(e))
    except SubjectAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error agregando materia al programa: {str(e)}")
        return internal_server_error_response()
    

@router.get(
    "/facultades/{faculty_id}/programas/{program_code}/materias",
    status_code=status.HTTP_200_OK,
    summary="Listar materias de un programa",
    description="Solo Administradores. Obtiene todas las materias de un programa con detalles completos",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_program_subjects(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    program_code: str = Path(..., description="Código del programa"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ProgramService()
        subjects = await service.get_program_subjects(faculty_id, program_code)
        
        return success_response(
            data=[subject.model_dump() for subject in subjects],
            message=f"Materias del programa {program_code} obtenidas correctamente"
        )
        
    except ProgramNotFoundException:
        return not_found_response("Programa", program_code)
    except Exception as e:
        logger.error(f"Error obteniendo materias del programa: {str(e)}")
        return internal_server_error_response()

@router.get(
    "/facultades/{faculty_id}/programas/{program_code}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener programa completo con materias",
    description="Solo Administradores. Obtiene un programa con todas sus materias pobladas",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_program_complete(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    program_code: str = Path(..., description="Código del programa"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = AcademicService()
        program = await service.get_program_with_subjects(faculty_id, program_code)
        
        return success_response(
            data=program.model_dump(),
            message="Programa con materias obtenido correctamente"
        )
        
    except ProgramNotFoundException:
        return not_found_response("Programa", program_code)
    except Exception as e:
        logger.error(f"Error obteniendo programa completo: {str(e)}")
        return internal_server_error_response()