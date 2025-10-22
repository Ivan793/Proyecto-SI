from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict
from datetime import datetime

from app.schemas.types import UserId
from app.schemas.user import UserBase
from app.core.constants import Defaults
from app.core.constants import ValidationMessages, Limits
from app.core.patterns import Patterns
import re


# ---------------------------
# BASE DEL INVITADO
# ---------------------------
class GuestBase(BaseModel):
    institucion_origen: Optional[str] = Field(default=None, description="Institución del invitado")
    motivo_visita: Optional[str] = Field(default=None, description="Motivo de la visita")
    activo: bool = Field(default=Defaults.ACTIVE_STATUS, description="Estado del invitado (activo/inactivo)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institucion_origen": "Universidad Nacional",
                "motivo_visita": "Conferencia académica",
                "activo": True
            }
        }
    )


# ---------------------------
# CREAR INVITADO CON USUARIO (CASCADA)
# ---------------------------
class GuestCreate(UserBase, GuestBase):
    contraseña: str = Field(..., description="Contraseña del invitado")

    @field_validator("correo")
    def validate_guest_email(cls, v):
        # Los invitados pueden usar cualquier dominio
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            raise ValueError(ValidationMessages.INVALID_EMAIL)
        return v

    @field_validator("contraseña")
    def validate_password_strength(cls, v):
        base_pattern = Patterns.PASSWORD.rstrip('$')
        full_pattern = f"{base_pattern}.{{{Limits.PASSWORD_MIN},{Limits.PASSWORD_MAX}}}$"
        if not re.match(full_pattern, v):
            raise ValueError(ValidationMessages.INVALID_PASSWORD)
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                # Datos del usuario
                "tipo_documento": "CC",
                "identificacion": "1234567890",
                "nombres": "Laura",
                "apellidos": "Castillo Ríos",
                "genero": "Mujer",
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "1998-05-17",
                "nacionalidad": "Colombiana",
                "pais_residencia": "Colombia",
                "departamento": "Atlántico",
                "municipio": "Barranquilla",
                "ciudad_residencia": "Barranquilla",
                "direccion_residencia": "Carrera 45 #32-15",
                "telefono": "+573002223334",
                "correo": "laura.castillo@gmail.com",
                "contraseña": "Invitado123#",
                "rol": "Invitado",
                # Datos del invitado
                "institucion_origen": "Universidad del Norte",
                "motivo_visita": "Foro de Tecnología",
                "activo": True
            }
        }
    )


# ---------------------------
# CREAR INVITADO CON USUARIO EXISTENTE
# ---------------------------
class GuestCreateExistingUser(GuestBase):
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
# ACTUALIZAR INVITADO
# ---------------------------
class GuestUpdate(BaseModel):
    institucion_origen: Optional[str] = None
    motivo_visita: Optional[str] = None
    activo: Optional[bool] = Field(default=None, description="Permite activar o desactivar el invitado")


# ---------------------------
# RESPUESTA DEL INVITADO
# ---------------------------
class GuestResponse(BaseModel):
    id_invitado: str
    id_usuario: UserId
    institucion_origen: Optional[str] = None
    motivo_visita: Optional[str] = None
    activo: bool = Field(default=Defaults.ACTIVE_STATUS, description="Estado actual del invitado")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------
# RESPUESTA INVITADO + USUARIO
# ---------------------------
class GuestWithUserResponse(BaseModel):
    invitado: GuestResponse
    usuario: Dict  # evita validación estricta del UserResponse

    model_config = ConfigDict(from_attributes=True)
