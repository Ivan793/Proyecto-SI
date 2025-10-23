from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.types import *
from app.schemas.user import UserCreate, UserResponse

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
    activo: Optional[StatusActive] = None

class StudentResponse(StudentBase):
    id_estudiante: StudentId
    id_usuario: UserId
    activo: StatusActive
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class StudentWithUserResponse(BaseModel):
    estudiante: StudentResponse
    usuario: UserResponse