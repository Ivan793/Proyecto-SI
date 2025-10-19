from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults

class TeacherBase(BaseModel):
    categoria_docente: TeacherCategoryType
    codigo_programa: ProgramCode
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria_docente": TeacherCategory.INTERNO,
                "codigo_programa": "ING01",
                "activo": True
            }
        }
    )

# Crear profesor con usuario existente
class TeacherCreateWithExistingUser(TeacherBase):
    id_usuario: UserId

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "L7Tz5A23fWx19oK9jK1a",
                "categoria_docente": TeacherCategory.INTERNO,
                "codigo_programa": "ING01"
            }
        }
    )

# Crear profesor CON usuario en cascada
class TeacherCreateWithUser(TeacherBase):
    usuario: UserCreate  # Datos completos del usuario a crear
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "usuario": {
                    "tipo_documento": "CC",
                    "identificacion": "1023456789",
                    "nombres": "María José",
                    "apellidos": "Pérez García",
                    "genero": "Mujer",
                    "identidad_sexual": "Heterosexual",
                    "fecha_nacimiento": "1985-03-15",
                    "direccion": "Calle 50 #30-20",
                    "pais": "Colombia",
                    "ciudad": "Valledupar",
                    "telefono": "+573001234567",
                    "correo": "maria.perez@unicesar.edu.co",
                    "contraseña": "Prof123#",
                    "rol": "Docente"
                },
                "categoria_docente": "Interno",
                "codigo_programa": "ING01"
            }
        }
    )

# Alias para mantener compatibilidad (usar la opción que prefieras como default)
TeacherCreate = TeacherCreateWithUser

class TeacherUpdate(BaseModel):
    categoria_docente: Optional[TeacherCategoryType] = None
    codigo_programa: Optional[ProgramCode] = None
    activo: Optional[bool] = None

class TeacherResponse(BaseModel):
    id_docente: TeacherId
    id_usuario: UserId
    categoria_docente: TeacherCategoryType
    codigo_programa: ProgramCode
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TeacherWithUserResponse(BaseModel):
    docente: TeacherResponse
    usuario: dict  # Cambiado a dict para evitar importación circular
