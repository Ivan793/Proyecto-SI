from typing import Any, Optional, List, TypeVar, Generic
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder

from app.schemas.common import (
    SuccessResponse,
    PaginatedResponse,
    PaginationMeta,
    MessageResponse,
    ErrorResponse,
    ErrorDetail
)

T = TypeVar('T')

# Crea una respuesta exitosa estandarizada usando el esquema SuccessResponse
def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200
) -> JSONResponse:
    response_model = SuccessResponse(
        status="success",
        message=message,
        data=data
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_model.model_dump(exclude_none=True))
    )

# Crea una respuesta simple con mensaje usando el esquema MessageResponse
def message_response(
    message: str,
    status_code: int = 200
) -> JSONResponse:
    response_model = MessageResponse(
        status="success",
        message=message
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_model.model_dump())
    )

# Crea una respuesta paginada estandarizada usando el esquema PaginatedResponse
def paginated_response(
    data: List[Any],
    page: int,
    limit: int,
    total_items: int
) -> JSONResponse:
    import math
    
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0
    has_next = page < total_pages
    has_prev = page > 1
    
    pagination_meta = PaginationMeta(
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
    
    response_model = PaginatedResponse(
        status="success",
        data=data,
        pagination=pagination_meta
    )
    
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response_model.model_dump())
    )

# Respuesta para recursos creados (201 Created)
def created_response(
    data: Any,
    message: str = "Recurso creado exitosamente"
) -> JSONResponse:
    return success_response(data, message, status_code=201)

# Respuesta para solicitudes aceptadas (202 Accepted)
def accepted_response(
    message: str = "Solicitud aceptada para procesamiento",
    data: Optional[Any] = None
) -> JSONResponse:
    if data:
        return success_response(data, message, status_code=202)
    else:
        return message_response(message, status_code=202)

# Respuesta sin contenido (204 No Content)
def no_content_response() -> JSONResponse:
    return JSONResponse(
        status_code=204,
        content=None
    )

# Crea una respuesta de error estandarizada usando el esquema ErrorResponse
def error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[List[dict]] = None,
    code: Optional[str] = None
) -> JSONResponse:
    error_details = None
    if errors:
        error_details = []
        for error in errors:
            if isinstance(error, dict):
                error_details.append(ErrorDetail(**error))
            else:
                error_details.append(error)
    
    response_model = ErrorResponse(
        status="error",
        message=message,
        errors=error_details,
        code=code,
        timestamp=datetime.now(timezone.utc)
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_model.model_dump(exclude_none=True))
    )


# Respuesta para errores 400 Bad Request
def bad_request_response(
    message: str = "Solicitud incorrecta",
    errors: Optional[List[dict]] = None,
    code: str = "BAD_REQUEST"
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=400,
        errors=errors,
        code=code
    )

# Respuesta para errores 401 Unauthorized
def unauthorized_response(
    message: str = "No autorizado",
    code: str = "UNAUTHORIZED"
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=401,
        code=code
    )

# Respuesta para errores 403 Forbidden
def forbidden_response(
    message: str = "No tiene permisos para realizar esta acción",
    code: str = "FORBIDDEN"
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=403,
        code=code
    )

# Respuesta para errores 404 Not Found
def not_found_response(
    resource: str = "Recurso",
    identifier: Optional[str] = None,
    code: str = "NOT_FOUND"
) -> JSONResponse:
    message = f"{resource} no encontrado"
    if identifier:
        message += f": {identifier}"
    
    return error_response(
        message=message,
        status_code=404,
        code=code
    )

# Respuesta para errores 409 Conflict
def conflict_response(
    message: str = "Conflicto con el estado actual del recurso",
    code: str = "CONFLICT"
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=409,
        code=code
    )

# Respuesta específica para errores de validación (422)
def validation_error_response(
    errors: List[dict],
    message: str = "Error de validación en los datos de entrada"
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=422,
        errors=errors,
        code="VALIDATION_ERROR"
    )

# Respuesta para errores 500 Internal Server Error
def internal_server_error_response(
    message: str = "Error interno del servidor",
    code: str = "INTERNAL_SERVER_ERROR"
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=500,
        code=code
    )

# Respuesta para errores 503 Service Unavailable
def service_unavailable_response(
    message: str = "Servicio no disponible temporalmente",
    code: str = "SERVICE_UNAVAILABLE"
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=503,
        code=code
    )


# Respuesta para actualizaciones exitosas
def updated_response(
    data: Any,
    message: str = "Recurso actualizado exitosamente"
) -> JSONResponse:
    return success_response(data, message, status_code=200)

# Respuesta para eliminaciones exitosas (NO CREO QUE SE USE)
def deleted_response(
    message: str = "Recurso eliminado exitosamente"
) -> JSONResponse:
    return message_response(message, status_code=200)

# Respuesta para login exitoso
def login_success_response(
    access_token: str,
    user_data: dict,
    refresh_token: Optional[str] = None,
    message: str = "Inicio de sesión exitoso"
) -> JSONResponse:
    data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }
    
    if refresh_token:
        data["refresh_token"] = refresh_token
    
    return success_response(data, message, status_code=200)

# Respuesta para logout exitoso
def logout_success_response(
    message: str = "Sesión cerrada exitosamente"
) -> JSONResponse:
    return message_response(message, status_code=200)


# Respuesta para operaciones asíncronas o en proceso

def operation_pending_response(
    operation_id: str,
    message: str = "Operación en proceso",
    estimated_completion: Optional[datetime] = None
) -> JSONResponse:
    data = {
        "operation_id": operation_id,
        "status": "processing"
    }
    
    if estimated_completion:
        data["estimated_completion"] = estimated_completion.isoformat()
    
    return success_response(data, message, status_code=202)


# Respuesta para exportaciones/listados listos para descargar

def export_ready_response(
    download_url: str,
    filename: str,
    message: str = "Exportación completada",
    expires_at: Optional[datetime] = None
) -> JSONResponse:
    data = {
        "download_url": download_url,
        "filename": filename,
        "status": "ready"
    }
    
    if expires_at:
        data["expires_at"] = expires_at.isoformat()
    
    return success_response(data, message, status_code=200)