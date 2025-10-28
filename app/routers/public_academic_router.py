from fastapi import APIRouter, Depends, Request, Path
from typing import Dict, Any
import logging

from app.services.academic_service import AcademicService, FacultyService, ProgramService
from app.dependencies.auth_dependencies import get_authenticated_user
from app.core.rate_limiter import auth_rate_limit
from app.utils.responses import success_response, not_found_response, internal_server_error_response
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.academic_exceptions import (
    FacultyNotFoundException, 
    ProgramNotFoundException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public-academico", tags=["Académico"])

# ==================== ÁRBOL COMPLETO ====================

@router.get(
    "/arbol-completo",
    summary="Obtener árbol académico completo",
    description=(
        "**Todos los roles autenticados**. "
        "Retorna la estructura completa: Facultades -> Programas -> Materias. "
        "Optimizado con consultas jerárquicas usando subcollections."
    ),
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_complete_academic_tree(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = AcademicService()
        academic_tree = await service.get_complete_academic_tree()
        
        return success_response(
            data=[faculty.model_dump() for faculty in academic_tree],
            message="Árbol académico completo obtenido correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo árbol académico: {str(e)}", exc_info=True)
        return internal_server_error_response()


# ==================== FACULTADES (PÚBLICAS) ====================

@router.get(
    "/facultades",
    summary="Listar todas las facultades",
    description="**Todos los roles autenticados**. Obtiene la lista de facultades disponibles",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_all_faculties(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
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
    summary="Obtener facultad con sus programas y materias",
    description=(
        "**Todos los roles autenticados**. "
        "Retorna una facultad con toda su estructura jerárquica: "
        "Programas y materias asociadas"
    ),
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_faculty_with_details(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = AcademicService()
        faculty = await service.get_faculty_with_details(faculty_id)
        
        return success_response(
            data=faculty.model_dump(),
            message="Facultad con detalles obtenida correctamente"
        )
        
    except FacultyNotFoundException:
        return not_found_response("Facultad", faculty_id)
    except Exception as e:
        logger.error(f"Error obteniendo facultad {faculty_id}: {str(e)}")
        return internal_server_error_response()


# ==================== PROGRAMAS (PÚBLICOS) ====================

@router.get(
    "/facultades/{faculty_id}/programas",
    summary="Obtener programas de una facultad",
    description="**Todos los roles autenticados**. Lista los programas de una facultad específica",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_programs_by_faculty(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
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
    summary="Obtener programa con sus materias",
    description=(
        "**Todos los roles autenticados**. "
        "Retorna un programa con todas sus materias asociadas"
    ),
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_program_with_subjects(
    request: Request,
    faculty_id: str = Path(..., description="Código de la facultad"),
    program_code: str = Path(..., description="Código del programa"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
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
        logger.error(f"Error obteniendo programa {program_code}: {str(e)}")
        return internal_server_error_response()