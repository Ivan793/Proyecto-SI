from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime

from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults

# ---------------------------
# Base del profesor
# ---------------------------
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

# ---------------------------
# Crear profesor con todos los campos de usuario + campos de profesor (CASCADA)
# ---------------------------
class TeacherCreateWithUser(UserCreate, TeacherBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                # Datos del usuario
                "tipo_documento": "CC",
                "identificacion": "1023456789",
                "nombres": "María José",
                "apellidos": "Pérez García",
                "genero": "Mujer",
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "1985-03-15",
                "nacionalidad": "Colombia",
                "pais_residencia": "Colombia",
                "departamento": "Cesar",
                "municipio": "Valledupar",
                "direccion_residencia": "Calle 50 #30-20",
                "telefono": "+573001234567",
                "correo": "maria.perez@unicesar.edu.co",
                "contraseña": "Prof123#",
                "rol": Role.DOCENTE,
                # Datos del profesor
                "categoria_docente": "Interno",
                "codigo_programa": "ING01",
                "activo": True
            }
        }
    )

# ---------------------------
# Crear profesor asignando a usuario existente
# ---------------------------
class TeacherCreateWithExistingUser(TeacherBase):
    id_usuario: UserId

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "123456",
                "categoria_docente": "Interno",
                "codigo_programa": "ING01",
                "activo": True
            }
        }
    )

# ---------------------------
# Actualizar profesor
# ---------------------------
class TeacherUpdate(BaseModel):
    categoria_docente: Optional[TeacherCategoryType] = None
    codigo_programa: Optional[ProgramCode] = None
    activo: Optional[bool] = None

# ---------------------------
# Respuesta del profesor
# ---------------------------
class TeacherResponse(BaseModel):
    id_docente: TeacherId
    id_usuario: UserId
    categoria_docente: TeacherCategoryType
    codigo_programa: ProgramCode
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ---------------------------
# Respuesta profesor con usuario
# ---------------------------
class TeacherWithUserResponse(BaseModel):
    docente: TeacherResponse
    usuario: Dict  # Se mantiene como dict para evitar importación circular

    model_config = ConfigDict(from_attributes=True)
