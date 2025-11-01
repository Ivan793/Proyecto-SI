from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

from app.schemas.types import FacultyId, FacultyName
from app.schemas.program import ProgramWithSubjects

class FacultyBase(BaseModel):
    nombre_facultad: FacultyName # type: ignore
    
    @field_validator("nombre_facultad")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre de la facultad no puede estar vacío")
        return v.title()

class FacultyCreate(FacultyBase):
    id_facultad: FacultyId # type: ignore
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_facultad": "FAC_ING",
                "nombre_facultad": "Ingenierías y Tecnologías"
            }
        }
    )

class FacultyUpdate(BaseModel):
    nombre_facultad: Optional[FacultyName] = None # type: ignore
    
    validate_name_not_empty = field_validator("nombre_facultad")(
        FacultyBase.validate_name_not_empty.__func__
    )

class FacultyResponse(FacultyBase):
    id_facultad: FacultyId # type: ignore
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id_facultad": "FAC_ING",
                "nombre_facultad": "Ingenierías y Tecnologías",
                "created_at": "2025-01-27T10:00:00Z",
                "updated_at": "2025-01-27T10:00:00Z"
            }
        }
    )

class FacultyWithPrograms(FacultyResponse):
    """Facultad con todos sus programas y materias"""
    programas: List[ProgramWithSubjects] = []