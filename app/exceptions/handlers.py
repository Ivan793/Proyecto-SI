from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime
import logging
import traceback

from .base_exceptions import AppException
from app.exceptions.teacher_subject_exceptions import (
    TeacherSubjectNotFoundException,
    TeacherSubjectAlreadyExistsException,
    TeacherSubjectAssignmentException,
    TeacherSubjectHasDependenciesException,
    TeacherNotAvailableException
)

from app.exceptions.event_exceptions import (
    EventNotFoundException,
    EventAlreadyExistsException,
    EventFullException,
    InvalidEventDatesException,
    InvalidEventStateTransitionException,
    EventNotActiveException
)
from app.exceptions.academic_exceptions import (
    FacultyNotFoundException,
    FacultyAlreadyExistsException,
    ProgramNotFoundException,
    ProgramAlreadyExistsException,
    InvalidFacultyException
)

from app.exceptions.research_exceptions import (
    ResearchLineNotFoundException,
    ResearchLineAlreadyExistsException,
    SubResearchLineNotFoundException,
    SubResearchLineAlreadyExistsException,
    InvalidResearchLineException,
    ThematicAreaNotFoundException,
    ThematicAreaAlreadyExistsException,
    InvalidSubResearchLineException
)

from app.exceptions.subject_exceptions import (
    SubjectNotFoundException,
    SubjectAlreadyExistsException,
    SubjectHasDependenciesException,
    InvalidSubjectStateException,
    MinimumGroupsRequiredException
)

from app.exceptions.group_exceptions import (
    GroupNotFoundException,
    GroupAlreadyExistsException,
    GroupHasStudentsException,
    GroupHasNoTeacherException,
    GroupHasNoSubjectException,
    GroupHasDependenciesException
)
from .teacher_exceptions import (
    TeacherNotFoundException, 
    TeacherAlreadyExistsException, 
    TeacherHasAssignmentsException
)
from .user_exceptions import (
    UserNotFoundException, 
    UserAlreadyExistsException,
    InvalidEmailDomainException
)
from .auth_exceptions import (
    InvalidCredentialsException,
    TokenExpiredException,
    InvalidTokenException,
    TokenNotFoundException,
    InsufficientPermissionsException,
    AccountDisabledException
)

logger = logging.getLogger(__name__)


def format_error_response(
    status_code: int,
    message: str,
    errors: list = None,
    code: str = None,
    **kwargs
) -> dict:
    """Formatea respuestas de error de manera consistente"""
    response = {
        "status": "error",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if errors:
        response["errors"] = errors
    
    if code:
        response["code"] = code
    
    # Agregar campos adicionales
    response.update(kwargs)
    
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Maneja excepciones personalizadas de la aplicación"""
    
    # Registrar el error según el nivel
    if exc.status_code >= 500:
        logger.error(
            f"AppException: {exc.message} | Status: {exc.status_code} | Path: {request.url.path}",
            extra={"details": exc.details},
            exc_info=True
        )
    else:
        logger.warning(
            f"AppException: {exc.message} | Status: {exc.status_code} | Path: {request.url.path}",
            extra={"details": exc.details}
        )
    
    response_data = {
        "status": "error",
        "message": exc.message,
        "code": getattr(exc, 'code', 'UNKNOWN_ERROR'),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Agregar detalles si existen
    if exc.details:
        response_data["details"] = exc.details
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Maneja errores de validación de Pydantic"""
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.info(
        f"ValidationError: {len(errors)} errores | Path: {request.url.path}",
        extra={"errors": errors}
    )
    
    response_data = {
        "status": "error",
        "message": "Datos de entrada inválidos",
        "errors": errors,
        "code": "VALIDATION_ERROR",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )



async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """Maneja errores de validación directos de Pydantic"""
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    response_data = format_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Datos de entrada inválidos",
        errors=errors,
        code="VALIDATION_ERROR"
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response_data
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Maneja excepciones genéricas no capturadas"""
    
    # Registrar el error completo
    logger.critical(
        f"Unhandled exception: {str(exc)} | Path: {request.url.path}",
        exc_info=True
    )
    
    response_data = {
        "status": "error",
        "message": "Error interno del servidor",
        "code": "INTERNAL_SERVER_ERROR",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """Registra todos los manejadores de excepciones en la aplicación FastAPI"""
    
    # Excepciones personalizadas
    app.add_exception_handler(AppException, app_exception_handler)
    
    # Excepciones de asignación docente-materia
    app.add_exception_handler(TeacherSubjectNotFoundException, app_exception_handler)
    app.add_exception_handler(TeacherSubjectAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(TeacherSubjectAssignmentException, app_exception_handler)
    app.add_exception_handler(TeacherSubjectHasDependenciesException, app_exception_handler)
    app.add_exception_handler(TeacherNotAvailableException, app_exception_handler)
    
    # Excepciones de eventos
    app.add_exception_handler(EventNotFoundException, app_exception_handler)
    app.add_exception_handler(EventAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(EventFullException, app_exception_handler)
    app.add_exception_handler(InvalidEventDatesException, app_exception_handler)
    app.add_exception_handler(InvalidEventStateTransitionException, app_exception_handler)
    app.add_exception_handler(EventNotActiveException, app_exception_handler)
    
    # Excepciones de investigación
    app.add_exception_handler(ResearchLineNotFoundException, app_exception_handler)
    app.add_exception_handler(ResearchLineAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(SubResearchLineNotFoundException, app_exception_handler)
    app.add_exception_handler(SubResearchLineAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(InvalidResearchLineException, app_exception_handler)
    app.add_exception_handler(ThematicAreaNotFoundException, app_exception_handler)
    app.add_exception_handler(ThematicAreaAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(InvalidSubResearchLineException, app_exception_handler)
    
    # Excepciones de materias
    app.add_exception_handler(SubjectNotFoundException, app_exception_handler)
    app.add_exception_handler(SubjectAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(SubjectHasDependenciesException, app_exception_handler)
    app.add_exception_handler(InvalidSubjectStateException, app_exception_handler)
    app.add_exception_handler(MinimumGroupsRequiredException, app_exception_handler)
    
    # Excepciones de grupos
    app.add_exception_handler(GroupNotFoundException, app_exception_handler)
    app.add_exception_handler(GroupAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(GroupHasStudentsException, app_exception_handler)
    app.add_exception_handler(GroupHasNoTeacherException, app_exception_handler)
    app.add_exception_handler(GroupHasNoSubjectException, app_exception_handler)
    app.add_exception_handler(GroupHasDependenciesException, app_exception_handler)

    # Excepciones específicas de teachers
    app.add_exception_handler(TeacherNotFoundException, app_exception_handler)
    app.add_exception_handler(TeacherAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(TeacherHasAssignmentsException, app_exception_handler)
    
    # Excepciones de usuarios
    app.add_exception_handler(UserNotFoundException, app_exception_handler)
    app.add_exception_handler(UserAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(InvalidEmailDomainException, app_exception_handler)
    
    # Excepciones de autenticación
    app.add_exception_handler(InvalidCredentialsException, app_exception_handler)
    app.add_exception_handler(TokenExpiredException, app_exception_handler)
    app.add_exception_handler(InvalidTokenException, app_exception_handler)
    app.add_exception_handler(TokenNotFoundException, app_exception_handler)
    app.add_exception_handler(InsufficientPermissionsException, app_exception_handler)
    app.add_exception_handler(AccountDisabledException, app_exception_handler)

    # Excepciones de facultad y programa
    app.add_exception_handler(FacultyNotFoundException, app_exception_handler)
    app.add_exception_handler(FacultyAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(ProgramNotFoundException, app_exception_handler)
    app.add_exception_handler(ProgramAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(InvalidFacultyException, app_exception_handler)

    # Excepciones de validación
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Excepción genérica (debe ser la última)
    app.add_exception_handler(Exception, generic_exception_handler)