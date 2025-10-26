from typing import Any, Optional, List, Dict
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder

from app.schemas.common import (
    SuccessResponse, PaginatedResponse, ErrorResponse, ErrorDetail,
    MessageResponse, PaginationMeta, IdResponse, CountResponse, BulkOperationResult
)
from app.core.response_codes import ResponseCode, ResponseMessage, HTTP_CODE_TO_RESPONSE_CODE


def _get_response_code(status_code: int) -> ResponseCode:
    """Obtiene el código de respuesta basado en el código HTTP"""
    return HTTP_CODE_TO_RESPONSE_CODE.get(status_code, ResponseCode.INTERNAL_ERROR)


def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200
) -> JSONResponse:
    """Respuesta exitosa estandarizada"""
    response_model = SuccessResponse(
        status="success",
        message=message or ResponseMessage.SUCCESS,
        data=data,
        code=_get_response_code(status_code)
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_model.model_dump(exclude_none=True))
    )


def paginated_response(
    data: List[Any],
    page: int,
    limit: int,
    total_items: int,
    message: Optional[str] = None
) -> JSONResponse:
    """Respuesta paginada estandarizada"""
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
        message=message or "Datos obtenidos correctamente",
        data=data,
        pagination=pagination_meta,
        code=ResponseCode.SUCCESS
    )
    
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response_model.model_dump())
    )


def error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[List[Dict]] = None,
    code: Optional[str] = None,
    path: Optional[str] = None
) -> JSONResponse:
    """Respuesta de error estandarizada"""
    error_details = None
    if errors:
        error_details = []
        for error in errors:
            error_details.append(ErrorDetail(**error))
    
    response_model = ErrorResponse(
        status="error",
        message=message,
        errors=error_details,
        code=code or _get_response_code(status_code),
        timestamp=datetime.now(timezone.utc),
        path=path
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_model.model_dump(exclude_none=True))
    )


# Respuestas específicas predefinidas
def created_response(
    data: Any,
    message: str = ResponseMessage.CREATED
) -> JSONResponse:
    return success_response(data, message, status_code=201)


def updated_response(
    data: Any,
    message: str = ResponseMessage.UPDATED
) -> JSONResponse:
    return success_response(data, message, status_code=200)


def deleted_response(
    message: str = ResponseMessage.DELETED
) -> JSONResponse:
    return message_response(message, status_code=200)


def message_response(
    message: str,
    status_code: int = 200
) -> JSONResponse:
    response_model = MessageResponse(
        status="success",
        message=message,
        code=_get_response_code(status_code)
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_model.model_dump())
    )


def id_response(
    resource_id: str,
    message: Optional[str] = None
) -> JSONResponse:
    response_model = SuccessResponse(
        status="success",
        message=message or ResponseMessage.CREATED,
        data=IdResponse(id=resource_id),
        code=ResponseCode.CREATED
    )
    
    return JSONResponse(
        status_code=201,
        content=jsonable_encoder(response_model.model_dump())
    )


def count_response(
    count: int,
    message: Optional[str] = None
) -> JSONResponse:
    response_model = SuccessResponse(
        status="success",
        message=message or "Conteo obtenido correctamente",
        data=CountResponse(count=count),
        code=ResponseCode.SUCCESS
    )
    
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response_model.model_dump())
    )


def bulk_operation_response(
    processed: int,
    successful: int,
    failed: int,
    errors: Optional[List[Dict]] = None,
    message: Optional[str] = None
) -> JSONResponse:
    response_model = SuccessResponse(
        status="success",
        message=message or "Operación por lotes completada",
        data=BulkOperationResult(
            processed=processed,
            successful=successful,
            failed=failed,
            errors=errors
        ),
        code=ResponseCode.SUCCESS
    )
    
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response_model.model_dump(exclude_none=True))
    )


# Respuestas de error específicas
def bad_request_response(
    message: str = ResponseMessage.VALIDATION_ERROR,
    errors: Optional[List[Dict]] = None,
    code: str = ResponseCode.VALIDATION_ERROR,
    path: Optional[str] = None
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=400,
        errors=errors,
        code=code,
        path=path
    )


def unauthorized_response(
    message: str = ResponseMessage.UNAUTHORIZED,
    code: str = ResponseCode.UNAUTHORIZED
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=401,
        code=code
    )


def forbidden_response(
    message: str = ResponseMessage.FORBIDDEN,
    code: str = ResponseCode.FORBIDDEN
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=403,
        code=code
    )


def not_found_response(
    resource: str = "Recurso",
    identifier: Optional[str] = None,
    code: str = ResponseCode.NOT_FOUND
) -> JSONResponse:
    message = f"{resource} no encontrado"
    if identifier:
        message += f": {identifier}"
    
    return error_response(
        message=message,
        status_code=404,
        code=code
    )


def conflict_response(
    message: str = ResponseMessage.ALREADY_EXISTS,
    code: str = ResponseCode.ALREADY_EXISTS
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=409,
        code=code
    )


def validation_error_response(
    errors: List[Dict],
    message: str = ResponseMessage.VALIDATION_ERROR
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=422,
        errors=errors,
        code=ResponseCode.VALIDATION_ERROR
    )


def internal_server_error_response(
    message: str = "Error interno del servidor",
    code: str = ResponseCode.INTERNAL_ERROR
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=500,
        code=code
    )


def service_unavailable_response(
    message: str = "Servicio no disponible temporalmente",
    code: str = ResponseCode.SERVICE_UNAVAILABLE
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=503,
        code=code
    )


def rate_limit_response(
    message: str = "Límite de peticiones excedido",
    code: str = ResponseCode.RATE_LIMIT_EXCEEDED
) -> JSONResponse:
    return error_response(
        message=message,
        status_code=429,
        code=code
    )