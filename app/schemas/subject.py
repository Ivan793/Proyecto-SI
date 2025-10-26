from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional

from app.schemas.types import *

class SubjectBase(BaseModel):
    nombre_materia: SubjectName
    ciclo_semestral: SubjectCycleType
    
    @field_validator("nombre_materia")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre de la materia no puede estar vacío")
        return v.title()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre_materia": "Programación III",
                "ciclo_semestral": SubjectCycle.PROFESIONAL
            }
        }
    )

class SubjectCreate(SubjectBase):
    codigo_materia: SubjectCode
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_materia": "PROG3",
                "nombre_materia": "Programación III",
                "ciclo_semestral": SubjectCycle.PROFESIONAL
            }
        }
    )

class SubjectUpdate(BaseModel):
    nombre_materia: Optional[SubjectName] = None
    ciclo_semestral: Optional[SubjectCycle] = None

    validate_name_not_empty = field_validator("nombre_materia")(
        SubjectBase.validate_name_not_empty.__func__
    )

class SubjectResponse(SubjectBase):
    codigo_materia: SubjectCode
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_materia": "PROG3",
                "nombre_materia": "Programación III",
                "ciclo_semestral": SubjectCycle.PROFESIONAL
            }
        }
    )

class SubjectSummary(BaseModel):
    codigo_materia: SubjectCode
    nombre_materia: SubjectName
    ciclo_semestral: SubjectCycleType
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_materia": "PROG3",
                "nombre_materia": "Programación III",
                "ciclo_semestral": SubjectCycle.PROFESIONAL
            }
        }
    )

