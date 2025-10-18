from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Annotated
from datetime import date


UserId = Annotated[str, Field(min_length=10, max_length=30, description="Unique system-generated identifier")]
DocumentType = Annotated[str, Field(pattern="^(CC|TI|CE|PTE|PAS)$", description="Document type: CC, TI, CE, PTE, PAS")]
Identification = Annotated[str, Field(min_length=6, max_length=20, pattern="^[A-Za-z0-9]+$", description="Official identification code")]
Name = Annotated[str, Field(min_length=2, max_length=30, description="User's first or last name")]
Gender = Annotated[str, Field(pattern="^(Hombre|Mujer|Hermafrodita)$", description="User gender")]
SexualIdentity = Annotated[str, Field(min_length=3, max_length=20, description="Sexual identity (e.g., Transgénero, Bisexual, etc.)")]
Address = Annotated[str, Field(min_length=5, max_length=50, pattern="^[A-Za-z0-9#\\-\\s,]+$", description="Home address")]
Country = Annotated[str, Field(min_length=2, max_length=50, description="Country of origin")]
City = Annotated[str, Field(min_length=2, max_length=30, description="City or municipality")]
Phone = Annotated[str, Field(pattern="^\\+?[0-9]{7,15}$", description="Phone number with optional country prefix")]
Role = Annotated[str, Field(pattern="^(Docente|Estudiante|Invitado|Egresado|Administrativo)$", description="User role in the system")]


class UserBase(BaseModel):
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
        return v

    @field_validator("contraseña")
    def validate_password_strength(cls, v):
        import re
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9@]).{8,12}$"
        if not re.match(pattern, v):
            raise ValueError("Password must contain uppercase, lowercase, number, and a special character (excluding @)")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "tipo_documento": "CC",
                "identificacion": "1023456789",
                "nombres": "David José",
                "apellidos": "Rodríguez González",
                "genero": "Hombre",
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "2000-06-03",
                "direccion": "Calle 45 #22-10, Barrio San José",
                "pais": "Colombia",
                "ciudad": "Valledupar",
                "telefono": "+57301343343",
                "correo": "david.rodriguez@unicesar.edu.co",
                "contraseña": "Sass344#",
                "rol": "Estudiante"
            }
        }
    }


class UserCreate(UserBase):
    pass


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
