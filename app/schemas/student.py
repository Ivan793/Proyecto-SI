from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults



# Base del estudiante

class StudentBase(BaseModel):
    codigo_programa: str = Field(..., description="Código del programa académico")
    semestre: int = Field(..., ge=1, le=20, description="Semestre actual del estudiante")
    anio_ingreso: int = Field(..., ge=2000, le=2100, description="Año de ingreso del estudiante")
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_programa": "ING01",
                "semestre": 4,
                "anio_ingreso": 2022,
                "activo": True
            }
        }
    )



# Crear estudiante con usuario existente
class StudentCreateWithExistingUser(StudentBase):
    id_usuario: str = Field(..., description="ID del usuario existente")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "vPz9eFj4K2mLx8R1aWc3",
                "codigo_programa": "ING01",
                "semestre": 5,
                "anio_ingreso": 2023
            }
        }
    )



# Crear estudiante con usuario nuevo (en cascada)
class StudentCreateWithUser(StudentBase):
    usuario: UserCreate = Field(..., description="Datos completos del usuario asociado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "usuario": {
                    "tipo_documento": "CC",
                    "identificacion": "1098456123",
                    "nombres": "Iván Camilo",
                    "apellidos": "Centeno Anthoine",
                    "genero": "Hombre",
                    "identidad_sexual": "Heterosexual",
                    "fecha_nacimiento": "2000-04-15",
                    "nacionalidad": "Colombiana",
                    "pais_residencia": "Colombia",
                    "departamento": "Cesar",
                    "municipio": "Valledupar",
                    "ciudad_residencia": "Valledupar",
                    "direccion_residencia": "Carrera 12 #15-34",
                    "telefono": "+573002003004",
                    "correo": "ivan.centeno@unicesar.edu.co",
                    "contraseña": "Est123#",
                    "rol": "Estudiante"
                },
                "codigo_programa": "ING02",
                "semestre": 3,
                "anio_ingreso": 2023
            }
        }
    )


# Alias para mantener compatibilidad
StudentCreate = StudentCreateWithUser



# Actualización de estudiante
class StudentUpdate(BaseModel):
    codigo_programa: Optional[str] = None
    semestre: Optional[int] = None
    anio_ingreso: Optional[int] = None
    activo: Optional[bool] = None



# Respuesta base

class StudentResponse(BaseModel):
    id_estudiante: str
    id_usuario: str
    codigo_programa: str
    semestre: int
    anio_ingreso: int
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)



# Respuesta con datos del usuario

class StudentWithUserResponse(BaseModel):
    estudiante: StudentResponse
    usuario: dict  # evita importación circular
