from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

from app.schemas.types import ProgramCode, ProgramName, FacultyId
from app.schemas.subject import SubjectSummary

class ProgramBase(BaseModel):
    nombre_programa: ProgramName
    id_facultad: FacultyId
    
    @field_validator("nombre_programa")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre del programa no puede estar vacío")
        return v.title()

class ProgramCreate(ProgramBase):
    codigo_programa: ProgramCode
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_programa": "ING_SIS",
                "nombre_programa": "Ingeniería de Sistemas",
                "id_facultad": "FAC_ING"
            }
        }
    )

class ProgramUpdate(BaseModel):
    nombre_programa: Optional[ProgramName] = None
    
    validate_name_not_empty = field_validator("nombre_programa")(
        ProgramBase.validate_name_not_empty.__func__
    )

class ProgramResponse(ProgramBase):
    codigo_programa: ProgramCode
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_programa": "ING_SIS",
                "nombre_programa": "Ingeniería de Sistemas",
                "id_facultad": "FAC_ING",
                "created_at": "2025-01-27T10:00:00Z",
                "updated_at": "2025-01-27T10:00:00Z"
            }
        }
    )

class ProgramWithSubjects(ProgramResponse):
    """Programa con todas sus materias asociadas"""
    materias: List[SubjectSummary] = []