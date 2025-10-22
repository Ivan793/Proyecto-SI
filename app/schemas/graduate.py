from pydantic import BaseModel, Field, ConfigDict, EmailStr, constr
from typing import Optional, Dict
from datetime import datetime
from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults


# ---------------------------
# Base del egresado
# ---------------------------
class GraduateBase(BaseModel):
    programa_academico: Optional[str] = Field(default=None, min_length=3, description="Programa académico cursado")
    año_graduacion: Optional[int] = Field(default=None, ge=1900, le=datetime.now().year, description="Año de graduación")
    titulo_obtenido: Optional[str] = Field(default=None, min_length=3, description="Título obtenido por el egresado")
    activo: bool = Field(default=Defaults.ACTIVE_STATUS, description="Estado activo o inactivo del egresado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "programa_academico": "Ingeniería de Sistemas",
                "año_graduacion": 2023,
                "titulo_obtenido": "Ingeniero de Sistemas",
                "activo": True
            }
        }
    )


# ---------------------------
# Crear egresado con usuario (CASCADA)
# ---------------------------
class GraduateCreate(UserCreate, GraduateBase):
    correo: EmailStr = Field(..., description="Correo institucional o personal del egresado")
    contraseña: constr(min_length=8) = Field(..., description="Contraseña segura del egresado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo_documento": "CC",
                "identificacion": "1002431808",
                "nombres": "David José",
                "apellidos": "Rodríguez González",
                "genero": "Hombre",
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "2000-06-03",
                "nacionalidad": "Colombiana",
                "pais_residencia": "Colombia",
                "departamento": "Cesar",
                "municipio": "Valledupar",
                "ciudad_residencia": "Valledupar",
                "direccion_residencia": "Calle 45 #22-10",
                "telefono": "+57301343343",
                "correo": "nathaly@unicesar.edu.co",
                "contraseña": "Egresado123#",
                "rol": "Egresado",
                "programa_academico": "Ingeniería de Sistemas",
                "año_graduacion": 2023,
                "titulo_obtenido": "Ingeniero de Sistemas",
                "activo": True
            }
        }
    )


# ---------------------------
# Crear egresado con usuario existente
# ---------------------------
class GraduateCreateExistingUser(GraduateBase):
    id_usuario: UserId

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "abc12345",
                "programa_academico": "Ingeniería Civil",
                "año_graduacion": 2022,
                "titulo_obtenido": "Ingeniero Civil",
                "activo": True
            }
        }
    )


# ---------------------------
# Actualizar egresado
# ---------------------------
class GraduateUpdate(BaseModel):
    programa_academico: Optional[str] = Field(default=None, min_length=3)
    año_graduacion: Optional[int] = Field(default=None, ge=1900, le=datetime.now().year)
    titulo_obtenido: Optional[str] = Field(default=None, min_length=3)
    activo: Optional[bool] = Field(default=None, description="Permite activar o desactivar al egresado")


# ---------------------------
# Respuesta de egresado
# ---------------------------
class GraduateResponse(BaseModel):
    id_egresado: str
    id_usuario: UserId
    programa_academico: Optional[str] = None
    año_graduacion: Optional[int] = None
    titulo_obtenido: Optional[str] = None
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------
# Respuesta egresado con usuario
# ---------------------------
class GraduateWithUserResponse(BaseModel):
    egresado: GraduateResponse
    usuario: Dict

    model_config = ConfigDict(from_attributes=True)
