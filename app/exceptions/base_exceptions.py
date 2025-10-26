from typing import Any, Optional, Dict
from fastapi import status


class AppException(Exception):
    """Excepción base de la aplicación"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Excepción para errores de validación"""
    
    def __init__(
        self,
        message: str = "Error de validación",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field = field
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {}
        )


class NotFoundException(AppException):
    """Excepción cuando un recurso no se encuentra"""
    
    def __init__(
        self,
        resource: str,
        identifier: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} con identificador '{identifier}' no encontrado"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {}
        )


class ConflictException(AppException):
    """Excepción para conflictos (recursos duplicados, etc.)"""
    
    def __init__(
        self,
        message: str,
        conflict_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.conflict_field = conflict_field
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {}
        )


class ForbiddenException(AppException):
    """Excepción cuando el usuario no tiene permisos"""
    
    def __init__(
        self,
        message: str = "No tiene permisos para realizar esta acción",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {}
        )


class DependencyException(AppException):
    """Excepción cuando hay dependencias que impiden una operación"""
    
    def __init__(
        self,
        message: str,
        dependencies: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.dependencies = dependencies or {}
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {}
        )


class DatabaseException(AppException):
    """Excepción para errores de base de datos"""
    
    def __init__(
        self,
        message: str = "Error al acceder a la base de datos",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {}
        )