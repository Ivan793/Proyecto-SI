from typing import Optional, Dict, Any
from fastapi import status
from .base_exceptions import AppException


class AuthException(AppException):
    """Excepción base para autenticación"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            details=details or {}
        )


class InvalidCredentialsException(AuthException):
    """Credenciales inválidas"""
    
    def __init__(self, message: str = "Credenciales inválidas"):
        super().__init__(message=message)


class TokenExpiredException(AuthException):
    """Token expirado"""
    
    def __init__(self, message: str = "El token ha expirado"):
        super().__init__(message=message)


class InvalidTokenException(AuthException):
    """Token inválido"""
    
    def __init__(self, message: str = "Token inválido o malformado"):
        super().__init__(message=message)


class TokenNotFoundException(AuthException):
    """Token no proporcionado"""
    
    def __init__(self, message: str = "Token no proporcionado en la solicitud"):
        super().__init__(message=message)


class InsufficientPermissionsException(AuthException):
    """Permisos insuficientes"""
    
    def __init__(
        self,
        message: str = "No tiene permisos suficientes para realizar esta acción",
        required_role: Optional[str] = None
    ):
        details = {"required_role": required_role} if required_role else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class AccountDisabledException(AuthException):
    """Cuenta deshabilitada"""
    
    def __init__(self, message: str = "La cuenta está deshabilitada"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class AccountPendingApprovalException(AuthException):
    """Cuenta pendiente de aprobación"""
    
    def __init__(self, message: str = "La cuenta está pendiente de aprobación"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )