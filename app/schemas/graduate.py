from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, Dict
from datetime import datetime
from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults

class GraduateBase(BaseModel):
    programa_academico: Optional[AcademicProgram] = None
    año_graduacion: Optional[GraduationYear] = None
    titulo_obtenido: Optional[DegreeTitle] = None
    activo: StatusActive = Defaults.ACTIVE_STATUS

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

class GraduateCreate(UserCreate, GraduateBase):
    correo: UserEmail
    contraseña: UserPassword

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

class GraduateUpdate(BaseModel):
    programa_academico: Optional[AcademicProgram] = None
    año_graduacion: Optional[GraduationYear] = None
    titulo_obtenido: Optional[DegreeTitle] = None
    activo: Optional[StatusActive] = None

class GraduateResponse(BaseModel):
    id_egresado: GraduateId
    id_usuario: UserId
    programa_academico: Optional[AcademicProgram] = None
    año_graduacion: Optional[GraduationYear] = None
    titulo_obtenido: Optional[DegreeTitle] = None
    activo: StatusActive = Defaults.ACTIVE_STATUS
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class GraduateWithUserResponse(BaseModel):
    egresado: GraduateResponse
    usuario: Dict

    model_config = ConfigDict(from_attributes=True)