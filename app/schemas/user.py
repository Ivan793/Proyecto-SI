from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, ClassVar
from datetime import datetime
import re

# Importar tipos Annotated
from app.schemas.types import *
from app.core.patterns import Patterns
from app.core.constants import ValidationMessages, Limits, Defaults

class UserBase(BaseModel):
<<<<<<< HEAD
    tipo_documento: DocumentType
    identificacion: Identification
    nombres: Name
    apellidos: Name
    genero: Gender
    identidad_sexual: SexualIdentity
    fecha_nacimiento: date
    direccion: Address
    pais: Country
    ciudad: City
    telefono: Phone
    correo: EmailStr = Field(..., max_length=30, description="User email address")
    contraseña: str = Field(..., min_length=8, max_length=12, description="User password")
    rol: Role

    # ✅ Corregido: se usa "info.data.get" en lugar de "values.get"
    @field_validator("correo")
    def validate_institutional_email(cls, v, info):
        rol = info.data.get("rol") if info.data else None
        if rol in ("Docente", "Estudiante") and not v.endswith("@unicesar.edu.co"):
            raise ValueError("Institutional email required (@unicesar.edu.co) for Docente or Estudiante roles")
=======
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
    contraseña: UserPassword
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
>>>>>>> origin/Mateo
        return v

    @field_validator("contraseña")
    def validate_password_strength(cls, v):
        # Usar pattern del Core pero construir la regex completa
        base_pattern = Patterns.PASSWORD.rstrip('$')
        full_pattern = f"{base_pattern}.{{{Limits.PASSWORD_MIN},{Limits.PASSWORD_MAX}}}$"
        if not re.match(full_pattern, v):
            raise ValueError(ValidationMessages.INVALID_PASSWORD)
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
                "contraseña": "Sass344#",
                "rol": Role.ESTUDIANTE
            }
        }
    )

class UserCreate(UserBase):
    pass

<<<<<<< HEAD

class UserUpdate(BaseModel):
    tipo_documento: Optional[DocumentType] = None
    identificacion: Optional[Identification] = None
    nombres: Optional[Name] = None
    apellidos: Optional[Name] = None
    genero: Optional[Gender] = None
    identidad_sexual: Optional[SexualIdentity] = None
    fecha_nacimiento: Optional[date] = None
    direccion: Optional[Address] = None
    pais: Optional[Country] = None
    ciudad: Optional[City] = None
    telefono: Optional[Phone] = None
    correo: Optional[EmailStr] = None
    contraseña: Optional[str] = None
    rol: Optional[Role] = None


class UserResponse(UserBase):
    id_usuario: str
=======
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
>>>>>>> origin/Mateo
