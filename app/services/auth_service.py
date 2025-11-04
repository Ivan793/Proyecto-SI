
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
from fastapi import Response
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
            activo = user.get("activo", True)
            
            if activo == False:
                logger.warning(f"Login fallido: cuenta inactiva - {correo}")
                raise AccountDisabledException()

            
            if activo != True:
                logger.warning(f"Login fallido: estado inválido '{activo}' - {correo}")
                raise AccountDisabledException(
                    f"Estado de cuenta inválido: {activo}"
                )
            # AUTENTICAR CON FIREBASE AUTHENTICATION
            try:
                firebase_response = self._authenticate_firebase(correo, password)
            except InvalidCredentialsException as e:
                logger.warning(f"Login fallido: Firebase auth falló - {correo}")
                raise e
            
            if correo != settings.ADMIN_DEFAULT_EMAIL:
                firebase_user = firebase_auth.get_user_by_email(correo)
                if not firebase_user.email_verified:
                    raise AccountPendingApprovalException(
                        "Debes verificar tu correo electrónico antes de iniciar sesión. "
                        "Revisa tu bandeja de entrada."
                    )
            
            # ACTUALIZAR ÚLTIMA CONEXIÓN
            try:
                user_id = user.get("id_usuario") or user.get("id")
                await self.user_repo.update(user_id, {
                    "ultima_conexion": datetime.now()
                })
            except Exception as e:
                logger.warning(f"No se pudo actualizar última conexión: {str(e)}")
            
            # PREPARAR DATOS DEL USUARIO
            user_data = self._prepare_minimal_user_data(user)
            
            logger.info(f"Login exitoso: {correo} (rol: {user.get('rol')})")
            
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
        

    async def send_email_verification(self, email: str) -> bool:
            """Envía email de verificación usando Firebase"""
            try:
                url = (
                    f"https://identitytoolkit.googleapis.com/v1/"
                    f"accounts:sendOobCode?key={settings.FIREBASE_API_KEY}"
                )
                
                # Primero obtener el idToken del usuario
                firebase_user = firebase_auth.get_user_by_email(email)
                
                # Generar un token temporal para enviar el email
                custom_token = firebase_auth.create_custom_token(firebase_user.uid)
                
                # Intercambiar por idToken
                sign_in_response = requests.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={settings.FIREBASE_API_KEY}",
                    json={"token": custom_token.decode(), "returnSecureToken": True}
                )
                
                if sign_in_response.status_code != 200:
                    logger.error(f"Error obteniendo idToken: {sign_in_response.text}")
                    return False
                
                id_token = sign_in_response.json().get("idToken")
                
                # Enviar email de verificación
                response = requests.post(
                    url,
                    json={
                        "requestType": "VERIFY_EMAIL",
                        "idToken": id_token
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Email de verificación enviado a: {email}")
                    return True
                else:
                    logger.error(f"Error enviando email de verificación: {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error enviando email de verificación: {str(e)}")
                return False



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
            if not user.get("activo", True):
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
    async def verify_firebase_token(self, token: str) -> Dict[str, Any]:
        """Verifica un token de Firebase y obtiene los datos del usuario"""
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            
            email = decoded_token.get("email")
            if not email:
                raise InvalidCredentialsException("Token no contiene email")
            
            user = await self.user_repo.get_by_field("correo", email)
            
            if not user:
                raise InvalidCredentialsException("Usuario no encontrado")
            
            if not user.get("activo", True):
                raise AccountDisabledException()
            
            return {
                "user_id": user.get("id_usuario") or user.get("id"),
                "email": user.get("correo"),
                "rol": user.get("rol"),
                "nombre_completo": f"{user.get('nombres')} {user.get('apellidos')}"
            }
            
        except firebase_auth.InvalidIdTokenError:
            raise InvalidCredentialsException("Token inválido")
        except firebase_auth.ExpiredIdTokenError:
            raise InvalidCredentialsException("Token expirado")
        except Exception as e:
            logger.error(f"Error verificando token: {str(e)}")
            raise InvalidCredentialsException("Error al verificar token")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresca un token de Firebase"""
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