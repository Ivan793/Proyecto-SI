from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from app.services.auth_service import AuthService
from app.exceptions.auth_exceptions import (
    TokenNotFoundException,
    InvalidCredentialsException,
    InsufficientPermissionsException,
    AccountDisabledException
)

logger = logging.getLogger(__name__)

# Esquema de seguridad Bearer
security = HTTPBearer()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Obtiene el usuario actual desde el token JWT de Firebase
    """
    if not credentials:
        raise TokenNotFoundException()
    
    token = credentials.credentials
    
    # Usar AuthService para verificar el token de Firebase
    auth_service = AuthService()
    
    try:
        user_info = await auth_service.verify_firebase_token(token)
        return user_info
    except Exception as e:
        logger.error(f"Error verificando token: {str(e)}")
        raise InvalidCredentialsException("Token inválido o expirado")


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Verifica que el usuario actual sea un administrador"""
    if current_user.get("rol") != "Administrativo":
        raise InsufficientPermissionsException(
            message="Se requieren permisos de administrador",
            required_role="Administrativo"
        )
    
    return current_user


async def get_current_teacher_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Verifica que el usuario actual sea un profesor"""
    if current_user.get("rol") != "Docente":
        raise InsufficientPermissionsException(
            message="Se requieren permisos de profesor",
            required_role="Docente"
        )
    
    return current_user


async def get_current_student_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Verifica que el usuario actual sea un estudiante"""
    if current_user.get("rol") not in ("Estudiante", "Egresado"):
        raise InsufficientPermissionsException(
            message="Se requieren permisos de estudiante",
            required_role="Estudiante"
        )
    
    return current_user

# Función para requerir múltiples roles
def require_roles(allowed_roles: list[str]):
    """Factory function para crear dependencias que requieran múltiples roles"""
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user_from_token)
    ) -> Dict[str, Any]:
        user_role = current_user.get("rol")
        if user_role not in allowed_roles:
            raise InsufficientPermissionsException(
                message=f"Se requiere uno de los roles: {', '.join(allowed_roles)}",
                required_role=", ".join(allowed_roles)
            )
        return current_user
    return role_checker

async def get_authenticated_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Verifica que el usuario esté autenticado (cualquier rol)"""
    return current_user


async def optional_authentication(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """Autenticación opcional - permite acceso sin token"""
    if not authorization:
        return None
    
    try:
        if not authorization.startswith("Bearer "):
            return None
        
        token = authorization.replace("Bearer ", "")
        
        auth_service = AuthService()
        user_info = await auth_service.verify_firebase_token(token)
        
        return user_info
        
    except Exception as e:
        logger.warning(f"Error en autenticación opcional: {str(e)}")
        return None


# ==================== VERIFICADORES DE PERMISOS ====================

class PermissionChecker:
    """Verificador de permisos basado en roles"""
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: Dict[str, Any] = Depends(get_current_user_from_token)
    ) -> Dict[str, Any]:
        """Verifica que el usuario tenga uno de los roles permitidos"""
        user_role = current_user.get("rol")
        
        if user_role not in self.allowed_roles:
            raise InsufficientPermissionsException(
                message=f"Se requiere uno de los siguientes roles: {', '.join(self.allowed_roles)}",
                required_role=", ".join(self.allowed_roles)
            )
        
        return current_user


# Instancias pre-configuradas
require_admin = PermissionChecker(["Administrativo"])
require_teacher = PermissionChecker(["Docente"])
require_student = PermissionChecker(["Estudiante", "Egresado"])
require_admin_or_teacher = PermissionChecker(["Administrativo", "Docente"])
require_any_authenticated = PermissionChecker(["Administrativo", "Docente", "Estudiante", "Egresado", "Invitado"])

