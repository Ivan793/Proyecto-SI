from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime

from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults


# ---------------------------
# Base del egresado
# ---------------------------
class GraduateBase(BaseModel):
    programa_academico: Optional[str] = Field(default=None, description="Programa académico cursado")
    año_graduacion: Optional[int] = Field(default=None, description="Año de graduación")
    titulo_obtenido: Optional[str] = Field(default=None, description="Título obtenido por el egresado")
    activo: bool = Field(default=Defaults.ACTIVE_STATUS, description="Estado activo o inactivo del egresado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "programa_academico": "Ingeniería de Sistemas",
                "año_graduacion": 2023,
                "titulo_obtenido": "Ingeniero de Sistemas",
                "activo": True
            }
        }
    )


# ---------------------------
# Crear egresado con usuario (CASCADA)
# NOTE: UserCreate primero (igual que GuestCreateWithUser)
# ---------------------------
class GraduateCreate(UserCreate, GraduateBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                # Datos de usuario
                "tipo_documento": "CC",
                "identificacion": "1023456789",
                "nombres": "David José",
                "apellidos": "Rodríguez González",
                "genero": "Hombre",
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "2000-06-03",
                "nacionalidad": "Colombia",
                "pais_residencia": "Colombia",
                "departamento": "Cesar",
                "municipio": "Valledupar",
                "direccion_residencia": "Calle 45 #22",
                "telefono": "+57301343343",
                "correo": "anderson.quintero@unicesar.edu.co",
                "contraseña": "Egresado123#",
                "rol": "Egresado",
                # Datos del egresado
                "programa_academico": "Ingeniería de Sistemas",
                "año_graduacion": 2023,
                "titulo_obtenido": "Ingeniero de Sistemas",
                "activo": True
            }
        }
    )


# ---------------------------
# Crear egresado con usuario existente
# ---------------------------
class GraduateCreateExistingUser(GraduateBase):
    id_usuario: UserId

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "abc12345",
                "programa_academico": "Ingeniería Civil",
                "año_graduacion": 2022,
                "titulo_obtenido": "Ingeniero Civil",
                "activo": True
            }
        }
    )


# ---------------------------
# Actualizar egresado
# ---------------------------
class GraduateUpdate(BaseModel):
    programa_academico: Optional[str] = None
    año_graduacion: Optional[int] = None
    titulo_obtenido: Optional[str] = None
    activo: Optional[bool] = Field(default=None, description="Permite activar o desactivar al egresado")


# ---------------------------
# Respuesta de egresado
# ---------------------------
class GraduateResponse(BaseModel):
    id_egresado: str
    id_usuario: UserId
    programa_academico: Optional[str] = None
    año_graduacion: Optional[int] = None
    titulo_obtenido: Optional[str] = None
    activo: bool = Field(default=Defaults.ACTIVE_STATUS, description="Estado actual del egresado")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------
# Respuesta egresado con usuario
# ---------------------------
class GraduateWithUserResponse(BaseModel):
    egresado: GraduateResponse
    usuario: Dict  # evita validación estricta del UserResponse (manejo tipo guest)

    model_config = ConfigDict(from_attributes=True)
