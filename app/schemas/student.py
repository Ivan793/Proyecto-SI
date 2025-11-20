from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Optional
from datetime import datetime
from app.schemas.types import *
from app.schemas.user import UserBasicInfo, UserCreate, UserResponse, UserUpdate

class StudentBase(BaseModel):
    codigo_programa: ProgramCode
    semestre: Semester
    anio_ingreso: YearOfEntry
    periodo: period

class StudentCreateWithUser(BaseModel):
    usuario: UserCreate
    codigo_programa: ProgramCode
    semestre: Semester
    anio_ingreso: YearOfEntry
    periodo: period
    model_config = ConfigDict(from_attributes=True)


class StudentUpdate(BaseModel):
    semestre: Optional[Semester] = None

    @field_validator('semestre')
    @classmethod
    def validate_semester_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 20):
            raise ValueError("El semestre debe estar entre 1 y 20")
        return v


class StudentProfileUpdate(BaseModel):
    """Esquema para actualizar perfil completo del estudiante"""
    datos_estudiante: Optional[StudentUpdate] = None
    datos_usuario: Optional[UserUpdate] = None

    @model_validator(mode='after')
    def validate_at_least_one_section(self) -> 'StudentProfileUpdate':
        """Valida que se proporcione al menos una sección para actualizar"""
        if not self.datos_estudiante and not self.datos_usuario:
            raise ValueError("Debe proporcionar datos del estudiante o del usuario para actualizar")
        return self
    
    model_config = ConfigDict(from_attributes=True)

class StudentResponse(StudentBase):
    id_estudiante: StudentId
    id_usuario: UserId
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class StudentWithUserResponse(BaseModel):
    estudiante: StudentResponse
    usuario: UserBasicInfo  # ← Usar el esquema centralizado

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estudiante": {
                    "id_estudiante": "est_123abc",
                    "id_usuario": "user_456def",
                    "codigo_programa": "ING02",
                    "semestre": 3,
                    "anio_ingreso": 2023,
                    "periodo": 2,
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00"
                },
                "usuario": {
                    "nombre_completo": "Juan Carlos Pérez González",
                    "identificacion": "1023456789",
                    "correo": "juan.perez@unicesar.edu.co",
                    "telefono": "+57301343343",
                    "activo": True
                }
            }
        }
    )

class StudentWithBasicUserResponse(BaseModel):
    id_estudiante: StudentId
    id_usuario: UserId
    codigo_programa: ProgramCode
    semestre: Semester
    anio_ingreso: YearOfEntry
    usuario: UserBasicInfo
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentWithFullUserResponse(BaseModel):
    estudiante: StudentResponse
    usuario: UserResponse

    model_config = ConfigDict(from_attributes=True)