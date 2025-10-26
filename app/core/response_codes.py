from enum import Enum
from typing import Dict, Any

class ResponseCode(str, Enum):
    # Éxito
    SUCCESS = "SUCCESS"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    ACCEPTED = "ACCEPTED"
    
    # Errores de validación
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    INVALID_PHONE = "INVALID_PHONE"
    INVALID_IDENTIFICATION = "INVALID_IDENTIFICATION"
    INVALID_NAME = "INVALID_NAME"
    INVALID_ADDRESS = "INVALID_ADDRESS"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Errores de autenticación y autorización
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    ACCOUNT_PENDING = "ACCOUNT_PENDING"
    
    # Errores de recursos
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    RESOURCE_IN_USE = "RESOURCE_IN_USE"
    
    # Errores del servidor
    INTERNAL_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Errores de base de datos
    DATABASE_ERROR = "DATABASE_ERROR"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

    #Errores de negocio
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INVALID_OPERATION = "INVALID_OPERATION"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    INVALID_STATE = "INVALID_STATE"



class ResponseMessage(str, Enum):
    # Mensajes de éxito
    SUCCESS = "Operación realizada exitosamente"
    CREATED = "Recurso creado exitosamente"
    UPDATED = "Recurso actualizado exitosamente"
    DELETED = "Recurso eliminado exitosamente"
    ACCEPTED = "Solicitud aceptada para procesamiento"
    
    # Mensajes de error
    VALIDATION_ERROR = "Error de validación en los datos de entrada"
    NOT_FOUND = "Recurso no encontrado"
    ALREADY_EXISTS = "El recurso ya existe"
    UNAUTHORIZED = "No autorizado"
    FORBIDDEN = "No tiene permisos para realizar esta acción"
    DATABASE_ERROR = "Error al acceder a la base de datos"
    INTERNAL_ERROR = "Error interno del servidor"
    RATE_LIMIT_EXCEEDED = "Límite de peticiones excedido"


# Mapeo de códigos HTTP a códigos de error personalizados
HTTP_CODE_TO_RESPONSE_CODE: Dict[int, ResponseCode] = {
    # Éxito
    200: ResponseCode.SUCCESS,
    201: ResponseCode.CREATED,
    202: ResponseCode.ACCEPTED,
    
    # Cliente
    400: ResponseCode.VALIDATION_ERROR,
    401: ResponseCode.UNAUTHORIZED,
    403: ResponseCode.FORBIDDEN,
    404: ResponseCode.NOT_FOUND,
    409: ResponseCode.ALREADY_EXISTS,
    422: ResponseCode.VALIDATION_ERROR,
    429: ResponseCode.RATE_LIMIT_EXCEEDED,
    
    # Servidor
    500: ResponseCode.INTERNAL_ERROR,
    503: ResponseCode.SERVICE_UNAVAILABLE,
}

# Mapeo de códigos de error a mensajes por defecto
CODE_TO_DEFAULT_MESSAGE: Dict[ResponseCode, str] = {
    ResponseCode.SUCCESS: ResponseMessage.SUCCESS,
    ResponseCode.CREATED: ResponseMessage.CREATED,
    ResponseCode.UPDATED: ResponseMessage.UPDATED,
    ResponseCode.DELETED: ResponseMessage.DELETED,
    
    ResponseCode.VALIDATION_ERROR: ResponseMessage.VALIDATION_ERROR,
    ResponseCode.NOT_FOUND: ResponseMessage.NOT_FOUND,
    ResponseCode.ALREADY_EXISTS: ResponseMessage.ALREADY_EXISTS,
    ResponseCode.UNAUTHORIZED: ResponseMessage.UNAUTHORIZED,
    ResponseCode.FORBIDDEN: ResponseMessage.FORBIDDEN,
    ResponseCode.INTERNAL_ERROR: ResponseMessage.INTERNAL_ERROR,
    ResponseCode.RATE_LIMIT_EXCEEDED: ResponseMessage.RATE_LIMIT_EXCEEDED,
}


def get_default_message_for_code(code: ResponseCode) -> str:
    """Obtiene el mensaje por defecto para un código de respuesta"""
    return CODE_TO_DEFAULT_MESSAGE.get(code, "Error desconocido")
