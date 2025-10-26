from enum import Enum
from typing import Dict, Any

class ResponseCode(str, Enum):
    # Éxito
    SUCCESS = "SUCCESS"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    
    # Errores de validación
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    
    # Errores de autenticación y autorización
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Errores de recursos
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    
    # Errores del servidor
    INTERNAL_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class ResponseMessage(str, Enum):
    # Mensajes de éxito
    SUCCESS = "Operación realizada exitosamente"
    CREATED = "Recurso creado exitosamente"
    UPDATED = "Recurso actualizado exitosamente"
    DELETED = "Recurso eliminado exitosamente"
    
    # Mensajes de error
    VALIDATION_ERROR = "Error de validación en los datos de entrada"
    NOT_FOUND = "Recurso no encontrado"
    ALREADY_EXISTS = "El recurso ya existe"
    UNAUTHORIZED = "No autorizado"
    FORBIDDEN = "No tiene permisos para realizar esta acción"


# Mapeo de códigos HTTP a códigos de error personalizados
HTTP_CODE_TO_RESPONSE_CODE: Dict[int, ResponseCode] = {
    200: ResponseCode.SUCCESS,
    201: ResponseCode.CREATED,
    400: ResponseCode.VALIDATION_ERROR,
    401: ResponseCode.UNAUTHORIZED,
    403: ResponseCode.FORBIDDEN,
    404: ResponseCode.NOT_FOUND,
    409: ResponseCode.ALREADY_EXISTS,
    422: ResponseCode.VALIDATION_ERROR,
    429: ResponseCode.RATE_LIMIT_EXCEEDED,
    500: ResponseCode.INTERNAL_ERROR,
    503: ResponseCode.SERVICE_UNAVAILABLE,
}