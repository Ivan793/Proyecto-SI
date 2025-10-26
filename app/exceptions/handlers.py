from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime
import logging

from .base_exceptions import AppException

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
    
    # Registrar el error
    logger.warning(
        f"AppException: {exc.message} | Status: {exc.status_code} | Path: {request.url.path}",
        extra={"details": exc.details}
    )
    
    response_data = format_error_response(
        status_code=exc.status_code,
        message=exc.message,
        **exc.details
    )
    
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
    logger.error(
        f"Unhandled exception: {str(exc)} | Path: {request.url.path}",
        exc_info=True
    )
    
    response_data = format_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Error interno del servidor",
        code="INTERNAL_SERVER_ERROR"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """Registra todos los manejadores de excepciones en la aplicación FastAPI"""
    
    # Excepciones personalizadas
    app.add_exception_handler(AppException, app_exception_handler)
    
    # Excepciones de validación
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Excepción genérica (debe ser la última)
    app.add_exception_handler(Exception, generic_exception_handler)