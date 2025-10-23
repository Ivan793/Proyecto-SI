from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from typing import Dict, Any
import logging

from app.repositories.user_repository import UserRepository
from app.repositories.student_repository import StudentRepository

logger = logging.getLogger(__name__)

security = HTTPBearer()


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
    """
    Verifica que el usuario actual sea un administrador.
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Diccionario con la información del administrador
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if current_user.get('rol') not in ['Administrador', 'Admin', 'Administrativo']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "mensaje": "Acceso denegado. Se requieren permisos de administrador"
            }
        )
    
    return current_user


async def get_current_student_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verifica que el usuario actual sea un estudiante y obtiene su información completa.
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Diccionario con información del usuario y estudiante
        
    Raises:
        HTTPException: Si el usuario no es estudiante
    """
    if current_user.get('rol') not in ['Estudiante', 'Egresado']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "mensaje": "Acceso denegado. Solo estudiantes pueden acceder"
            }
        )
    
    # Obtener información del estudiante
    student_repo = StudentRepository()
    estudiante = await student_repo.get_student_by_user_id(
        current_user['id_usuario']
    )
    
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": "Informacion de estudiante no encontrada"
            }
        )
    
    # Verificar que el estudiante esté activo
    if not estudiante.get('activo', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "mensaje": "Estudiante inactivo"
            }
        )
    
    # Combinar información del usuario y estudiante
    return {
        **current_user,
        'id_estudiante': estudiante['id_estudiante'],
        'codigo_programa': estudiante.get('codigo_programa'),
        'semestre': estudiante.get('semestre')
    }


async def get_current_teacher_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verifica que el usuario actual sea un docente.
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Diccionario con la información del docente
        
    Raises:
        HTTPException: Si el usuario no es docente
    """
    if current_user.get('rol') != 'Docente':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "mensaje": "Acceso denegado. Solo docentes pueden acceder"
            }
        )
    
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