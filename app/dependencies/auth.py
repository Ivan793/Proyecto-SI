# app/dependencies/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Obtiene el usuario actual y verifica que sea administrador.
    Versión simplificada para desarrollo.
    """
    try:
        # Verificar token con Firebase
        token = credentials.credentials
        decoded_token = firebase_auth.verify_id_token(token)
        
        # En desarrollo, aceptamos cualquier usuario autenticado
        # En producción, aquí verificarías el rol de administrador
        logger.info(f"Usuario autenticado: {decoded_token.get('email')}")
        
        return {
            "uid": decoded_token.get('uid'),
            "email": decoded_token.get('email'),
            "role": "admin"  # Mock para desarrollo
        }
    
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido"
        )
    
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación expirado"
        )
    
    except Exception as e:
        logger.error(f"Error verificando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación"
        )