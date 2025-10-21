from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime

from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults


# ---------------------------
# Base del invitado
# ---------------------------
class GuestBase(BaseModel):
    institucion_origen: Optional[str] = Field(default=None, description="Institución de la cual proviene el invitado")
    motivo_visita: Optional[str] = Field(default=None, description="Motivo de la visita del invitado")
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institucion_origen": "Universidad del Norte",
                "motivo_visita": "Conferencia sobre Inteligencia Artificial",
                "activo": True
            }
        }
    )


# ---------------------------
# Crear invitado con todos los campos de usuario + campos de invitado (CASCADA)
# ---------------------------
class GuestCreateWithUser(UserCreate, GuestBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                # Datos del usuario
                "tipo_documento": "CC",
                "identificacion": "1001234567",
                "nombres": "Laura",
                "apellidos": "Castillo Ríos",
                "genero": "Mujer",
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "1992-11-20",
                "nacionalidad": "Colombia",
                "pais_residencia": "Colombia",
                "departamento": "Atlántico",
                "municipio": "Barranquilla",
                "direccion_residencia": "Carrera 45 #32-15",
                "telefono": "+573002223334",
                "correo": "Anderson@uninorte.edu.co",
                "contraseña": "Invitado123#",
                "rol": "Invitado",
                # Datos del invitado
                "institucion_origen": "Universidad del Norte",
                "motivo_visita": "Conferencia sobre IA aplicada a la educación",
                "activo": True
            }
        }
    )


# ---------------------------
# Crear invitado asignando a usuario existente
# ---------------------------
class GuestCreateWithExistingUser(GuestBase):
    id_usuario: UserId

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "abc12345",
                "institucion_origen": "SENA",
                "motivo_visita": "Capacitación docente",
                "activo": True
            }
        }
    )


# ---------------------------
# Actualizar invitado
# ---------------------------
class GuestUpdate(BaseModel):
    institucion_origen: Optional[str] = None
    motivo_visita: Optional[str] = None
    activo: Optional[bool] = None


# ---------------------------
# Respuesta del invitado
# ---------------------------
class GuestResponse(BaseModel):
    id_invitado: str
    id_usuario: UserId
    institucion_origen: Optional[str] = None
    motivo_visita: Optional[str] = None
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------
# Respuesta invitado con usuario
# ---------------------------
class GuestWithUserResponse(BaseModel):
    invitado: GuestResponse
    usuario: Dict  # Se mantiene como dict para evitar importación circular

    model_config = ConfigDict(from_attributes=True)
