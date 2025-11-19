from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict
from datetime import datetime
from app.schemas.types import *
from app.schemas.user import UserCreate  
from app.core.constants import ValidationMessages, Limits
from app.core.patterns import Patterns
import re
from app.core.enums import Sector


class GuestBase(BaseModel):
    institucion_origen: Optional[Institution] = None
    nombre_empresa: Optional[str] = None  
    id_sector: Optional[Sector] = None       

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institucion_origen": "Universidad Nacional",
                "nombre_empresa": "Tech Solutions S.A.S",
                "id_sector": "SEC12345"
            }
        }
    )

class GuestCreate(UserCreate, GuestBase):  # ✅ hereda de UserCreate
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
                "tipo_documento": DocumentType.CC,
                "identificacion": "1234567890",
                "primer_nombre": "Laura",
                "segundo_nombre": "",
                "primer_apellido": "Castillo",
                "segundo_apellido": "Ríos",
                "sexo": Sex.MUJER,
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
                "rol": Role.INVITADO,
                "institucion_origen": "Universidad del Norte",
                "nombre_empresa": "Tech Solutions S.A.S",
                "id_sector": Sector.EMPRESARIAL
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
                "nombre_empresa": None,
                "id_sector": None
            }
        }
    )

# ✅ Aquí añadimos los campos del usuario para actualizar
class GuestUpdate(BaseModel):
    institucion_origen: Optional[Institution] = None
    nombre_empresa: Optional[str] = None
    id_sector: Optional[Sector] = None
    primer_nombre: Optional[UserName] = None
    segundo_nombre: Optional[UserName] = None
    primer_apellido: Optional[UserName] = None
    segundo_apellido: Optional[UserName] = None
    sexo: Optional[UserSex] = None
    identidad_sexual: Optional[UserSexualIdentity] = None
    fecha_nacimiento: Optional[datetime] = None
    nacionalidad: Optional[UserNationality] = None
    pais_residencia: Optional[UserCountry] = None
    departamento: Optional[UserDepartment] = None
    municipio: Optional[UserMunicipality] = None
    ciudad_residencia: Optional[UserCity] = None
    direccion_residencia: Optional[UserAddress] = None
    telefono: Optional[UserPhone] = None
    contraseña: Optional[UserPassword] = None
    activo: Optional[StatusActive] = None
    razon_desactivacion: Optional[ReasonText] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institucion_origen": "Universidad del Norte",
                "nombre_empresa": "Tech Solutions S.A.S",
                "id_sector": Sector.SOCIAL,
                "primer_nombre": "Laura",
                "segundo_nombre": "María",
                "primer_apellido": "Castillo",
                "segundo_apellido": "Ríos",
                "sexo": "Mujer",
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "1998-05-17",
                "nacionalidad": "Colombiana",
                "pais_residencia": "Colombia",
                "departamento": "Atlántico",
                "municipio": "Barranquilla",
                "ciudad_residencia": "Barranquilla",
                "direccion_residencia": "Carrera 45 #32-15",
                "telefono": "+573002223334",
                "activo": True
            }
        }
    )

class GuestResponse(BaseModel):
    id_invitado: GuestId
    id_usuario: UserId
    institucion_origen: Optional[Institution] = None
    nombre_empresa: Optional[str] = None
    id_sector: Optional[Sector] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class GuestWithUserResponse(BaseModel):
    invitado: GuestResponse
    usuario: Dict

    model_config = ConfigDict(from_attributes=True)
