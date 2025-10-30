from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.core.validators import TeacherValidatorMixin
from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults


class TeacherBase(BaseModel, TeacherValidatorMixin):
    categoria_docente: TeacherCategoryType
    codigo_programa: ProgramCode

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria_docente": TeacherCategory.INTERNO,
                "codigo_programa": "ING01",
                "activo": True
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
                    "identificacion": "1231271982",
                    "nombres": "Camila Andrea",
                    "apellidos": "Torres Palomino",
                    "sexo": "Mujer",
                    "identidad_sexual": "Heterosexual",
                    "fecha_nacimiento": "1980-05-15",
                    "nacionalidad": "Colombiana",
                    "pais_residencia": "Colombia",
                    "departamento": "Cesar",
                    "municipio": "Valledupar",
                    "ciudad_residencia": "Valledupar",
                    "direccion_residencia": "Calle 45 #22-10, Barrio San Jose",
                    "telefono": "+573112345678",
                    "correo": "camila.torres@unicesar.edu.co",
                    "contraseña": "Prof123#",
                    "rol": "Docente"
                },
                "categoria_docente": "Interno",
                "codigo_programa": "ING02"
            }
        }
    )


# Alias para mantener compatibilidad (usar la opción que prefieras como default)
TeacherCreate = TeacherCreateWithUser


class TeacherUpdate(BaseModel):
    categoria_docente: Optional[TeacherCategoryType] = None
    codigo_programa: Optional[ProgramCode] = None


class TeacherResponse(BaseModel):
    id_docente: TeacherId
    id_usuario: UserId
    categoria_docente: TeacherCategoryType
    codigo_programa: ProgramCode
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TeacherWithUserResponse(BaseModel):
    docente: TeacherResponse
    usuario: dict  # Cambiado a dict para evitar importación circular