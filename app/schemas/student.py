from pydantic import BaseModel, Field
from typing import Optional


class StudentBase(BaseModel):
    id_usuario: str = Field(..., max_length=30)
    codigo_programa: str = Field(..., max_length=10)
    semestre: int
    anio_ingreso: int


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id_estudiante: str

    class Config:
        orm_mode = True
