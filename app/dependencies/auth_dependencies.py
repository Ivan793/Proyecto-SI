from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from typing import Dict, Any, Optional, Union, List
import logging

from app.repositories.user_repository import UserRepository
from app.repositories.student_repository import StudentRepository

logger = logging.getLogger(__name__)

security = HTTPBearer()

class InsufficientPermissionsException(HTTPException):
    """Exception to indicate insufficient permissions with a standardized detail payload."""
    def __init__(self, message: str = "Se requieren permisos insuficientes", required_role: Optional[Union[str, List[str]]] = None):
        detail = {
            "status": "error",
            "mensaje": message
        }
        if required_role is not None:
            detail["required_role"] = required_role
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Obtiene el usuario actual desde el token JWT de Firebase.
    
    Args:
        credentials: Credenciales del bearer token
        
    Returns:
        Diccionario con la información del usuario
        
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        # Verificar token con Firebase
        token = credentials.credentials
        decoded_token = firebase_auth.verify_id_token(token)
        
        # Obtener UID del usuario
        uid = decoded_token['uid']
        
        # Obtener información del usuario desde Firestore
        user_repo = UserRepository()
        user = await user_repo.get_by_id(uid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "mensaje": "Usuario no encontrado en la base de datos"
                }
            )
        
        # Validar que el usuario esté activo
        if user.get('estado') != 'ACTIVO':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "error",
                    "mensaje": "Usuario inactivo"
                }
            )
        
        return user
    
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "mensaje": "Token de autenticacion invalido"
            }
        )
    
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "mensaje": "Token de autenticacion expirado"
            }
        )
    
    except Exception as e:
        logger.error(f"Error verificando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "mensaje": "Error de autenticacion"
            }
        )
    

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Alias para get_current_user - mantiene compatibilidad con código existente.
    
    Args:
        credentials: Credenciales del bearer token
        
    Returns:
        Diccionario con la información del usuario
    """
    return await get_current_user(credentials)


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
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


# ==================== NUEVAS FUNCIONES PARA COMPATIBILIDAD ====================

class PermissionChecker:
    """Verificador de permisos basado en roles"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Verifica que el usuario tenga uno de los roles permitidos"""
        user_role = current_user.get("rol")
        
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "error",
                    "mensaje": f"Se requiere uno de los siguientes roles: {', '.join(self.allowed_roles)}"
                }
            )
        
        return current_user


# Instancias pre-configuradas
require_admin = PermissionChecker(["Administrador", "Admin", "Administrativo"])
require_teacher = PermissionChecker(["Docente"])
require_student = PermissionChecker(["Estudiante", "Egresado"])
require_admin_or_teacher = PermissionChecker(["Administrador", "Admin", "Administrativo", "Docente"])
require_any_authenticated = PermissionChecker(["Administrativo", "Docente", "Estudiante", "Egresado", "Invitado"])




# ==================== FUNCIONES ALIAS ADICIONALES ====================

async def get_admin_or_teacher_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verifica que el usuario sea administrador o docente.
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Diccionario con la información del usuario
        
    Raises:
        HTTPException: Si el usuario no es admin ni docente
    """
    if current_user.get('rol') not in ['Administrador', 'Admin', 'Administrativo', 'Docente']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "mensaje": "Acceso denegado. Se requieren permisos de administrador o docente"
            }
        )
    
    return current_user