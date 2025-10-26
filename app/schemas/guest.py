from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict
from datetime import datetime
from app.schemas.types import *
from app.schemas.user import UserBase
from app.core.constants import Defaults, ValidationMessages, Limits
from app.core.patterns import Patterns
import re

class GuestBase(BaseModel):
    institucion_origen: Optional[Institution] = None
    motivo_visita: Optional[VisitReason] = None
    activo: StatusActive = Defaults.ACTIVE_STATUS

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institucion_origen": "Universidad Nacional",
                "motivo_visita": "Conferencia académica",
                "activo": True
            }
        }
    )

class GuestCreate(UserBase, GuestBase):
    contraseña: UserPassword

    @field_validator("correo")
    def validate_guest_email(cls, v):
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
                "institucion_origen": "Universidad del Norte",
                "motivo_visita": "Foro de Tecnología",
                "activo": True
            }
        }
    )

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

class GuestUpdate(BaseModel):
    institucion_origen: Optional[Institution] = None
    motivo_visita: Optional[VisitReason] = None
    activo: Optional[StatusActive] = None

class GuestResponse(BaseModel):
    id_invitado: GuestId
    id_usuario: UserId
    institucion_origen: Optional[Institution] = None
    motivo_visita: Optional[VisitReason] = None
    activo: StatusActive = Defaults.ACTIVE_STATUS
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class GuestWithUserResponse(BaseModel):
    invitado: GuestResponse
    usuario: Dict

    model_config = ConfigDict(from_attributes=True)