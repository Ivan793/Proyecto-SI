from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.schemas.user import UserCreate, UserResponse
from app.schemas.types import *

class StudentBase(BaseModel):
    codigo_programa: str = Field(..., description="Código del programa académico")
    semestre: int = Field(..., ge=1, le=20, description="Semestre actual del estudiante")
    anio_ingreso: int = Field(..., ge=2000, le=2100, description="Año de ingreso del estudiante")

class StudentCreateWithUser(BaseModel):
    usuario: UserCreate
    codigo_programa: str
    semestre: int
    anio_ingreso: int

class StudentCreateWithExistingUser(BaseModel):
    id_usuario: str
    codigo_programa: str
    semestre: int
    anio_ingreso: int

class StudentUpdate(BaseModel):
    activo: Optional[bool] = None

class StudentResponse(StudentBase):
    id_estudiante: str
    id_usuario: str
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class StudentWithUserResponse(BaseModel):
    estudiante: StudentResponse
    usuario: UserResponse