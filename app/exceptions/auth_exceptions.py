from typing import Optional, Dict, Any
from fastapi import status
from .base_exceptions import AppException
from app.core.response_codes import ResponseCode


class AuthException(AppException):
    """Excepción base para autenticación"""
    
    def __init__(
        self,
        message: str = None,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None,
        code: Optional[ResponseCode] = None
    ):
        if code is None:
            code = ResponseCode.UNAUTHORIZED
            
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            code=code
        )


class InvalidCredentialsException(AuthException):
    """Credenciales inválidas"""
    
    def __init__(self, message: str = "Credenciales inválidas"):
        super().__init__(
            message=message,
            code=ResponseCode.UNAUTHORIZED
        )


class TokenExpiredException(AuthException):
    """Token expirado"""
    
    def __init__(self, message: str = "El token ha expirado"):
        super().__init__(
            message=message,
            code=ResponseCode.EXPIRED_TOKEN
        )


class InvalidTokenException(AuthException):
    """Token inválido"""
    
    def __init__(self, message: str = "Token inválido o malformado"):
        super().__init__(
            message=message,
            code=ResponseCode.INVALID_TOKEN
        )


class TokenNotFoundException(AuthException):
    """Token no proporcionado"""
    
    def __init__(self, message: str = "Token no proporcionado en la solicitud"):
        super().__init__(
            message=message,
            code=ResponseCode.UNAUTHORIZED
        )


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
            details=details,
            code=ResponseCode.INSUFFICIENT_PERMISSIONS
        )


class AccountDisabledException(AuthException):
    """Cuenta deshabilitada"""
    
    def __init__(self, message: str = "La cuenta está deshabilitada"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code=ResponseCode.ACCOUNT_DISABLED
        )


class AccountPendingApprovalException(AuthException):
    """Cuenta pendiente de aprobación"""
    
    def __init__(self, message: str = "La cuenta está pendiente de aprobación"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code=ResponseCode.ACCOUNT_PENDING
        )


class FirebaseAuthException(AuthException):
    """Error de Firebase Authentication"""
    
    def __init__(self, message: str, firebase_error: Optional[str] = None):
        details = {"firebase_error": firebase_error} if firebase_error else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            code=ResponseCode.EXTERNAL_SERVICE_ERROR
        )