from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.types import *
from app.schemas.user import UserBasicInfo, UserCreate, UserResponse

class StudentBase(BaseModel):
    codigo_programa: ProgramCode
    semestre: Semester
    anio_ingreso: YearOfEntry

class StudentCreateWithUser(BaseModel):
    usuario: UserCreate
    codigo_programa: ProgramCode
    semestre: Semester
    anio_ingreso: YearOfEntry

class StudentCreateWithExistingUser(BaseModel):
    id_usuario: UserId
    codigo_programa: ProgramCode
    semestre: Semester
    anio_ingreso: YearOfEntry

class StudentUpdate(BaseModel):
    codigo_programa: Optional[ProgramCode] = None
    activo: Optional[StatusActive] = None

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