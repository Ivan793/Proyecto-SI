
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
import requests
from firebase_admin import auth as firebase_auth

from app.core.config import settings
from app.repositories.base_repository import BaseRepository
from app.core.firebase import Collections
from app.exceptions.auth_exceptions import (
    InvalidCredentialsException,
    AccountDisabledException,
    AccountPendingApprovalException
)

logger = logging.getLogger(__name__)


class AuthService:
    """Servicio centralizado de autenticación para todos los roles"""
    
    def __init__(self):
        self.user_repo = BaseRepository(Collections.USUARIOS)

    def _prepare_minimal_user_data(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id_usuario": user.get("id_usuario") or user.get("id"),
            "correo": user.get("correo"),
            "rol": user.get("rol"),
        }

# Login universal para todos los roles del sistema
    async def login(
        self,
        correo: str,
        password: str,
        required_role: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # VERIFICAR QUE EL USUARIO EXISTE EN FIRESTORE
            user = await self.user_repo.get_by_field("correo", correo)
            
            if not user:
                logger.warning(f"Login fallido: usuario no existe - {correo}")
                raise InvalidCredentialsException("Credenciales inválidas")
            
            # VERIFICAR ROL SI SE ESPECIFICÓ
            user_role = user.get("rol")
            if required_role and user_role != required_role:
                logger.warning(
                    f"Login fallido: rol incorrecto - {correo} "
                    f"(esperado: {required_role}, tiene: {user_role})"
                )
                raise InvalidCredentialsException(
                    f"No tiene permisos de {required_role}"
                )
            
            # VERIFICAR ESTADO DE LA CUENTA
            estado = user.get("estado", "").upper()
            
            if estado == "INACTIVO":
                logger.warning(f"Login fallido: cuenta inactiva - {correo}")
                raise AccountDisabledException()
            
            if estado == "PENDIENTE":
                logger.warning(f"Login fallido: cuenta pendiente - {correo}")
                raise AccountPendingApprovalException()
            
            if estado != "ACTIVO":
                logger.warning(f"Login fallido: estado inválido '{estado}' - {correo}")
                raise AccountDisabledException(
                    f"Estado de cuenta inválido: {estado}"
                )
            
            # AUTENTICAR CON FIREBASE AUTHENTICATION
            try:
                firebase_response = self._authenticate_firebase(correo, password)
            except InvalidCredentialsException as e:
                logger.warning(f"Login fallido: Firebase auth falló - {correo}")
                raise e
            
            # ACTUALIZAR ÚLTIMA CONEXIÓN
            try:
                user_id = user.get("id_usuario") or user.get("id")
                await self.user_repo.update(user_id, {
                    "ultima_conexion": datetime.now(timezone.utc)
                })
            except Exception as e:
                logger.warning(f"No se pudo actualizar última conexión: {str(e)}")
            
            # PREPARAR DATOS DEL USUARIO
            user_data = self._prepare_minimal_user_data(user)
            
            logger.info(f"Login exitoso: {correo} (rol: {user_role})")
            
            return {
                "access_token": firebase_response["idToken"],
                "refresh_token": firebase_response.get("refreshToken"),
                "token_type": "bearer",
                "expires_in": int(firebase_response.get("expiresIn", 3600)),
                "user": user_data
            }
            
        except (InvalidCredentialsException, AccountDisabledException, 
                AccountPendingApprovalException):
            raise
        except Exception as e:
            logger.error(f"Error inesperado en login: {str(e)}", exc_info=True)
            raise InvalidCredentialsException("Error durante la autenticación")

# Autentica usando Firebase REST API
    def _authenticate_firebase(self, email: str, password: str) -> Dict[str, Any]:
        try:
            url = (
                f"https://identitytoolkit.googleapis.com/v1/"
                f"accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}"
            )
            
            response = requests.post(
                url,
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "")
                
                # Mensajes más específicos según el error de Firebase
                if "INVALID_PASSWORD" in error_msg or "INVALID_LOGIN_CREDENTIALS" in error_msg:
                    raise InvalidCredentialsException("Contraseña incorrecta")
                elif "EMAIL_NOT_FOUND" in error_msg:
                    raise InvalidCredentialsException("Usuario no encontrado")
                elif "USER_DISABLED" in error_msg:
                    raise AccountDisabledException()
                elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_msg:
                    raise InvalidCredentialsException(
                        "Demasiados intentos fallidos. Intente más tarde"
                    )
                else:
                    raise InvalidCredentialsException("Error de autenticación")
            
            return response.json()
            
        except requests.Timeout:
            logger.error("Timeout conectando con Firebase Auth")
            raise InvalidCredentialsException("Timeout de autenticación")
        except requests.RequestException as e:
            logger.error(f"Error conectando con Firebase: {str(e)}")
            raise InvalidCredentialsException("Error de conexión")



# Verifica un token de Firebase y obtiene los datos del usuario
    async def verify_firebase_token(self, token: str) -> Dict[str, Any]:
        try:
            # Verificar token con Firebase Admin SDK
            decoded_token = firebase_auth.verify_id_token(token)
            
            # Obtener email del token
            email = decoded_token.get("email")
            if not email:
                raise InvalidCredentialsException("Token no contiene email")
            
            # Obtener usuario de Firestore
            user = await self.user_repo.get_by_field("correo", email)
            
            if not user:
                raise InvalidCredentialsException("Usuario no encontrado")
            
            # Verificar estado activo
            if user.get("estado") != "ACTIVO":
                raise AccountDisabledException()
            
            return {
                "user_id": user.get("id_usuario") or user.get("id"),
                "email": user.get("correo"),
                "rol": user.get("rol"),
                "estado": user.get("estado"),
                "nombre_completo": f"{user.get('nombres')} {user.get('apellidos')}"
            }
            
        except firebase_auth.InvalidIdTokenError:
            raise InvalidCredentialsException("Token inválido")
        except firebase_auth.ExpiredIdTokenError:
            raise InvalidCredentialsException("Token expirado")
        except Exception as e:
            logger.error(f"Error verificando token: {str(e)}")
            raise InvalidCredentialsException("Error al verificar token")

# Refresca un token de Firebase
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:

        try:
            url = (
                f"https://securetoken.googleapis.com/v1/token"
                f"?key={settings.FIREBASE_API_KEY}"
            )
            
            response = requests.post(
                url,
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                },
                timeout=10
            )
            
            if response.status_code != 200:
                raise InvalidCredentialsException("Token de refresco inválido")
            
            data = response.json()
            
            return {
                "access_token": data.get("id_token"),
                "refresh_token": data.get("refresh_token"),
                "token_type": "bearer",
                "expires_in": int(data.get("expires_in", 3600))
            }
            
        except requests.RequestException as e:
            logger.error(f"Error refrescando token: {str(e)}")
            raise InvalidCredentialsException("Error al refrescar token")