from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults


# BASE DEL ESTUDIANTE
class StudentBase(BaseModel):
    codigo_programa: str = Field(..., description="Código del programa académico")
    semestre: int = Field(..., ge=1, le=20, description="Semestre actual del estudiante")
    anio_ingreso: int = Field(..., ge=2000, le=2100, description="Año de ingreso del estudiante")
    periodo: int = Field(..., ge=1, le=2, description="Periodo académico actual (1 o 2)")
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_programa": "ING01",
                "semestre": 4,
                "anio_ingreso": 2022,
                "periodo": 1,
                "activo": True
            }
        }
    )



#  CREAR ESTUDIANTE CON USUARIO EXISTENTE

class StudentCreateWithExistingUser(StudentBase):
    id_usuario: str = Field(..., description="ID del usuario existente")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "vPz9eFj4K2mLx8R1aWc3",
                "codigo_programa": "ING01",
                "semestre": 5,
                "anio_ingreso": 2023,
                "periodo": 2
            }
        }
    )



# CREAR ESTUDIANTE CON USUARIO NUEVO (EN CASCADA)

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
                "anio_ingreso": 2023,
                "periodo": 1
            }
        }
    )


# Alias para mantener compatibilidad
StudentCreate = StudentCreateWithUser


#  ACTUALIZAR ESTUDIANTE

class StudentUpdate(BaseModel):
    codigo_programa: Optional[str] = None
    semestre: Optional[int] = None
    anio_ingreso: Optional[int] = None
    periodo: Optional[int] = Field(None, ge=1, le=2, description="Periodo académico actual")
    activo: Optional[bool] = None



#  RESPUESTA BASE
class StudentResponse(BaseModel):
    id_estudiante: str
    id_usuario: str
    codigo_programa: str
    semestre: int
    anio_ingreso: int
    periodo: int
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


#  RESPUESTA CON DATOS DEL USUARIO
class StudentWithUserResponse(BaseModel):
    estudiante: StudentResponse
    usuario: dict  # evita importación circular
