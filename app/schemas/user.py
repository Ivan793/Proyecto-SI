from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, ClassVar
from datetime import datetime
import re

# Importar tipos Annotated
from app.schemas.types import *
from app.core.patterns import Patterns
from app.core.constants import ValidationMessages, Limits, Defaults

class UserBase(BaseModel):
    tipo_documento: UserDocumentType
    identificacion: UserIdentification
    nombres: UserName
    apellidos: UserName
    genero: UserGender
    identidad_sexual: UserSexualIdentity
    fecha_nacimiento: datetime
    direccion: UserAddress
    pais: UserCountry
    ciudad: UserCity
    telefono: UserPhone
    correo: UserEmail
    rol: UserRole
    
    # Dominios permitidos por rol
    ALLOWED_DOMAINS: ClassVar = {
        Role.DOCENTE: ["@unicesar.edu.co", "@prof.unicesar.edu.co"],
        Role.ESTUDIANTE: ["@unicesar.edu.co"],
        Role.ADMINISTRATIVO: ["@unicesar.edu.co"]
    }
    
    @field_validator("correo")
    def validate_institutional_email(cls, v, info):
        rol = info.data.get("rol")
        if rol in cls.ALLOWED_DOMAINS:
            allowed_domains = cls.ALLOWED_DOMAINS[rol]
            if not any(v.endswith(domain) for domain in allowed_domains):
                raise ValueError(f"Correo institucional requerido ({', '.join(allowed_domains)}) para rol {rol}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo_documento": DocumentType.CC,
                "identificacion": "1023456789",
                "nombres": "David José",
                "apellidos": "Rodríguez González",
                "genero": Gender.HOMBRE,
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "2000-06-03",
                "direccion": "Calle 45 #22-10, Barrio San José",
                "pais": "Colombia",
                "ciudad": "Valledupar",
                "telefono": "+57301343343",
                "correo": "david.rodriguez@unicesar.edu.co",
                "rol": Role.ESTUDIANTE
            }
        }
    )

class UserCreate(UserBase):
    contraseña: UserPassword
    @field_validator("contraseña")
    def validate_password_strength(cls, v):
        base_pattern = Patterns.PASSWORD.rstrip('$')
        full_pattern = f"{base_pattern}.{{{Limits.PASSWORD_MIN},{Limits.PASSWORD_MAX}}}$"
        if not re.match(full_pattern, v):
            raise ValueError(ValidationMessages.INVALID_PASSWORD)
        return v

class UserUpdate(BaseModel):    
    tipo_documento: Optional[UserDocumentType] = None
    identificacion: Optional[UserIdentification] = None
    nombres: Optional[UserName] = None
    apellidos: Optional[UserName] = None
    genero: Optional[UserGender] = None
    identidad_sexual: Optional[UserSexualIdentity] = None
    fecha_nacimiento: Optional[datetime] = None
    direccion: Optional[UserAddress] = None
    pais: Optional[UserCountry] = None
    ciudad: Optional[UserCity] = None
    telefono: Optional[UserPhone] = None
    correo: Optional[UserEmail] = None
    contraseña: Optional[UserPassword] = None
    rol: Optional[UserRole] = None

class UserResponse(UserBase):    
    id_usuario: UserId
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
