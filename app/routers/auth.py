"""
Router de autenticación unificado para todos los roles del sistema
"""
from fastapi import APIRouter, Depends, status, Request, Body
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any, Optional
import logging

from app.core.rate_limiter import auth_rate_limit
from app.services.auth_service import AuthService
from app.dependencies.auth_dependencies import get_current_user_from_token
from app.utils.responses import (
    success_response,
    unauthorized_response,
    internal_server_error_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.auth_exceptions import (
    InvalidCredentialsException,
    AccountDisabledException,
    AccountPendingApprovalException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ==================== SCHEMAS ====================

class LoginRequest(BaseModel):
    """Esquema universal para login"""
    
    correo: EmailStr = Field(..., description="Correo electrónico del usuario")
    password: str = Field(
        ...,
        min_length=8,
        max_length=12,
        description="Contraseña del usuario"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "correo": "admin@unicesar.edu.co",
                    "password": "Admin123#"
                },
                {
                    "correo": "profesor@unicesar.edu.co",
                    "password": "Prof123#"
                },
                {
                    "correo": "estudiante@unicesar.edu.co",
                    "password": "Stud123#"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="Token JWT de acceso")
    refresh_token: str = Field(..., description="Token para refrescar sesión")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    user: Dict[str, Any] = Field(
        ...,
        description="Datos mínimos del usuario (solo id, correo, rol)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGci...",
                "refresh_token": "AMf-vBw9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id_usuario": "yH0onViXLoO4cHkgxpUXqpZDmK32",
                    "correo": "maria.perez@unicesar.edu.co",
                    "rol": "Docente"
                }
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Esquema para refrescar token"""

    refresh_token: str = Field(..., description="Token de refresco")


def _create_login_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea una respuesta de login segura.
    Solo incluye datos mínimos necesarios para el frontend.
    """
    user_data = result.get("user", {})

    nombre = user_data.get("nombre")
    if nombre:
        message = f"Bienvenido, {nombre}"
    else:
        message = "Inicio de sesión exitoso"

    return success_response(
        data={
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),
            "token_type": result.get("token_type", "bearer"),
            "expires_in": result.get("expires_in", 3600),
            "user": user_data
        },
        message=message
    )


# ==================== ENDPOINTS ====================

@router.post(
    "/login",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Login universal para todos los roles",
    description="""
    Endpoint único de autenticación para todos los roles del sistema:
    - Administrativo
    - Docente
    - Estudiante
    - Egresado
    - Invitado

    El sistema detecta automáticamente el rol del usuario y valida sus permisos.
    """,
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def universal_login(
        request: Request,
        credentials: LoginRequest
) -> Dict[str, Any]:
    try:
        auth_service = AuthService()

        result = await auth_service.login(
            correo=credentials.correo,
            password=credentials.password
        )

        return _create_login_response(result)

    except InvalidCredentialsException as e:
        return unauthorized_response(message="Credenciales inválidas")
    except AccountDisabledException as e:
        return unauthorized_response(
            message="Cuenta inactiva. Contacte al administrador"
        )
    except AccountPendingApprovalException as e:
        return unauthorized_response(
            message="Su cuenta está pendiente de aprobación"
        )
    except Exception as e:
        logger.error(f"Error inesperado en login: {str(e)}", exc_info=True)
        return internal_server_error_response(
            message="Error en el sistema. Intente más tarde"
        )


@router.post(
    "/login/admin",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Login específico para administradores",
    description="Login que valida explícitamente que el usuario sea Administrativo",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def admin_login(
        request: Request,
        credentials: LoginRequest
) -> Dict[str, Any]:
    try:
        auth_service = AuthService()

        result = await auth_service.login(
            correo=credentials.correo,
            password=credentials.password,
            required_role="Administrativo"
        )

        return _create_login_response(result)

    except InvalidCredentialsException as e:
        return unauthorized_response(message=str(e))
    except AccountDisabledException as e:
        return unauthorized_response(message=str(e))
    except Exception as e:
        logger.error(f"Error en admin login: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.post(
    "/login/teacher",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Login específico para docentes",
    description="Login que valida explícitamente que el usuario sea Docente",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def teacher_login(
        request: Request,
        credentials: LoginRequest
) -> Dict[str, Any]:
    try:
        auth_service = AuthService()

        result = await auth_service.login(
            correo=credentials.correo,
            password=credentials.password,
            required_role="Docente"
        )
        
        return _create_login_response(result)
        
    except InvalidCredentialsException as e:
        return unauthorized_response(message=str(e))
    except AccountDisabledException as e:
        return unauthorized_response(message=str(e))
    except Exception as e:
        logger.error(f"Error en teacher login: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.post(
    "/login/student",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Login específico para estudiantes",
    description="Login que valida explícitamente que el usuario sea Estudiante o Egresado",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def student_login(
        request: Request,
        credentials: LoginRequest
) -> Dict[str, Any]:
    try:
        auth_service = AuthService()

        result = await auth_service.login(
            correo=credentials.correo,
            password=credentials.password
        )

        user_role = result["user"]["rol"]
        if user_role not in ["Estudiante", "Egresado"]:
            return unauthorized_response(
                message="Este login es solo para estudiantes y egresados"
            )

        return _create_login_response(result)

    except InvalidCredentialsException as e:
        return unauthorized_response(message=str(e))
    except AccountDisabledException as e:
        return unauthorized_response(message=str(e))
    except Exception as e:
        logger.error(f"Error en student login: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.post(
    "/refresh",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Refrescar token de acceso",
    description="Obtiene un nuevo access_token usando el refresh_token",
    responses=ResponseDocumentation.get_standard_responses()
)
async def refresh_access_token(
        request: Request,
        refresh_data: RefreshTokenRequest
) -> Dict[str, Any]:
    try:
        auth_service = AuthService()
        result = await auth_service.refresh_token(refresh_data.refresh_token)

        return success_response(
            data=result,
            message="Token refrescado exitosamente"
        )

    except InvalidCredentialsException as e:
        return unauthorized_response(message=str(e))
    except Exception as e:
        logger.error(f"Error refrescando token: {str(e)}", exc_info=True)
        return internal_server_error_response()


@router.get(
    "/me",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Obtener información completa del usuario autenticado",
    description="Obtiene todos los datos del usuario autenticado y sus datos específicos según el rol (Egresado, Estudiante, Docente, Invitado o Administrativo).",
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_current_user_info(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """
    Retorna toda la información del usuario autenticado (campos completos del usuario)
    y la información de su rol asociado (Egresado, Estudiante, Docente, Invitado, Administrativo).
    """
    try:
        from app.repositories.user_repository import UserRepository
        from app.repositories.graduate_repository import GraduateRepository
        from app.repositories.student_repository import StudentRepository
        from app.repositories.guest_repository import GuestRepository
        from app.repositories.teacher_repository import TeacherRepository

        user_repo = UserRepository()
        rol = current_user.get("rol")
        user_id = current_user.get("user_id")

        # Obtener usuario completo desde Firestore
        user = await user_repo.get_by_id(user_id)
        if not user:
            return unauthorized_response(message="Usuario no encontrado en Firestore")

        # Asegurar incluir todos los campos definidos en UserBase
        user_data = {
            "id_usuario": user.get("id_usuario"),
            "tipo_documento": user.get("tipo_documento"),
            "identificacion": user.get("identificacion"),
            "primer_nombre": user.get("primer_nombre"),
            "segundo_nombre": user.get("segundo_nombre"),
            "primer_apellido": user.get("primer_apellido"),
            "segundo_apellido": user.get("segundo_apellido"),
            "sexo": user.get("sexo"),
            "identidad_sexual": user.get("identidad_sexual"),
            "fecha_nacimiento": user.get("fecha_nacimiento"),
            "nacionalidad": user.get("nacionalidad"),
            "pais_residencia": user.get("pais_residencia"),
            "departamento": user.get("departamento"),
            "municipio": user.get("municipio"),
            "ciudad_residencia": user.get("ciudad_residencia"),
            "direccion_residencia": user.get("direccion_residencia"),
            "telefono": user.get("telefono"),
            "correo": user.get("correo"),
            "rol": user.get("rol"),
            "activo": user.get("activo"),
            "razon_desactivacion": user.get("razon_desactivacion"),
            "ultima_conexion": user.get("ultima_conexion"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at")
        }

        # Datos específicos del rol
        role_data = None
        if rol == "Egresado":
            grad_repo = GraduateRepository()
            role_data = await grad_repo.get_graduate_by_user_id(user_id)
        elif rol == "Estudiante":
            student_repo = StudentRepository()
            role_data = await student_repo.get_student_by_user_id(user_id)
        elif rol == "Docente":
            teacher_repo = TeacherRepository()
            role_data = await teacher_repo.get_teacher_by_user_id(user_id)
        elif rol == "Invitado":
            guest_repo = GuestRepository()
            role_data = await guest_repo.get_guest_by_user_id(user_id)
        elif rol == "Administrativo":
            role_data = {"mensaje": "Rol administrativo, sin colección asociada"}

        # Armar respuesta final
        full_data = {
            "usuario": user_data,
            "rol": rol,
            "datos_rol": role_data or {}
        }

        return success_response(
            data=full_data,
            message=f"Información completa del usuario ({rol}) obtenida correctamente"
        )

    except Exception as e:
        logger.error(f"Error obteniendo info completa de usuario: {str(e)}", exc_info=True)
        return internal_server_error_response()



@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión",
    description="Cierra la sesión del usuario actual",
    responses=ResponseDocumentation.get_standard_responses()
)
async def logout(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    try:
        logger.info(f"Logout de usuario: {current_user.get('email')}")

        return success_response(
            data=None,
            message="Sesión cerrada exitosamente"
        )

    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return internal_server_error_response()