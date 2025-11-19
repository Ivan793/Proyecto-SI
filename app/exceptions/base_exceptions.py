from typing import Any, Optional, Dict
from fastapi import status

from app.core.response_codes import ResponseCode, get_default_message_for_code


class AppException(Exception):
    """Excepción base de la aplicación"""
    
    def __init__(
        self,
        message: str = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.INTERNAL_ERROR
    ):
        # Si no se proporciona mensaje, usar el por defecto del código
        if message is None:
            message = get_default_message_for_code(code)
            
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"{self.code}: {self.message} (Status: {self.status_code})"


class ValidationException(AppException):
    """Excepción para errores de validación"""
    
    def __init__(
        self,
        message: str = None,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.VALIDATION_ERROR
    ):
        self.field = field
        
        # Agregar información del campo a los detalles
        if field and details is None:
            details = {"field": field}
        elif field:
            details["field"] = field
            
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            code=code
        )


class NotFoundException(AppException):
    """Excepción cuando un recurso no se encuentra"""
    
    def __init__(
        self,
        resource: str,
        identifier: str,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.NOT_FOUND
    ):
        message = f"{resource} con identificador '{identifier}' no encontrado"
        
        if details is None:
            details = {}
        details.update({
            "resource": resource,
            "identifier": identifier
        })
            
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            code=code
        )


class ConflictException(AppException):
    """Excepción para conflictos (recursos duplicados, etc.)"""
    
    def __init__(
        self,
        message: str,
        conflict_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.ALREADY_EXISTS
    ):
        self.conflict_field = conflict_field
        
        if conflict_field and details is None:
            details = {"conflict_field": conflict_field}
        elif conflict_field:
            details["conflict_field"] = conflict_field
            
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            code=code
        )


class ForbiddenException(AppException):
    """Excepción cuando el usuario no tiene permisos"""
    
    def __init__(
        self,
        message: str = None,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.FORBIDDEN
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            code=code
        )


class DependencyException(AppException):
    """Excepción cuando hay dependencias que impiden una operación"""
    
    def __init__(
        self,
        message: str,
        dependencies: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.DEPENDENCY_ERROR
    ):
        self.dependencies = dependencies or {}
        
        if details is None:
            details = {}
        details["dependencies"] = self.dependencies
            
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            code=code
        )


class DatabaseException(AppException):
    """Excepción para errores de base de datos"""
    
    def __init__(
        self,
        message: str = None,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.DATABASE_ERROR
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            code=code
        )


class BusinessRuleException(AppException):
    """Excepción para violaciones de reglas de negocio"""
    
    def __init__(
        self,
        message: str,
        rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        code: ResponseCode = ResponseCode.BUSINESS_RULE_VIOLATION
    ):
        self.rule = rule
        
        if rule and details is None:
            details = {"rule": rule}
        elif rule:
            details["rule"] = rule
            
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            code=code
        )


class TransactionException(DatabaseException):
    """
    Excepción lanzada cuando ocurre un error durante una transacción en Firestore.

    Args:
        message: Mensaje descriptivo del error.
        details: Información adicional opcional (por ejemplo, IDs o datos relacionados).
    """
    def __init__(self, message="Error en transacción de Firestore", details=None):
        super().__init__(message=message, details=details or {})