"""
Esquemas Pydantic para Grupos Académicos con validación de docente
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.core.constants import Defaults
from app.schemas.types import GroupCode, StatusActive, SubjectCode, UserId


class GroupBase(BaseModel):
    codigo_grupo: GroupCode
    

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_grupo": 1
            }
        }
    )

class GroupCreate(BaseModel):
    codigo_grupo: GroupCode
    codigo_materia: SubjectCode

    @field_validator("codigo_grupo")
    @classmethod
    def validate_group_code(cls, v: int) -> int:
        """Valida que el código de grupo sea positivo"""
        if v <= 0:
            raise ValueError("El código de grupo debe ser un número positivo")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "codigo_grupo": 101,
                "id_docente": "L7Tz5A23fWx19oK9jK1a"
            }
        }
    }


class GroupUpdate(BaseModel):
    codigo_materia: Optional[SubjectCode] = None
    codigo_grupo: Optional[GroupCode] = None
    activo: StatusActive = Field(default=Defaults.ACTIVE_STATUS)

    model_config = ConfigDict(
    from_attributes=True,
    json_schema_extra={
        "example": {
            "codigo_materia": "MAT101",
            "activo": True
        }
    }
)



class GroupResponse(BaseModel):
    codigo_grupo: GroupCode
    codigo_materia: Optional[SubjectCode] = None
    activo: StatusActive = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GroupWithSubjectResponse(GroupResponse):
    codigo_materia: Optional[SubjectCode] = None
    nombre_materia: Optional[str] = None
    total_estudiantes: int = Field(default=0, ge=0)
    
    # Información del docente desde TeacherSubject
    docentes_asignados: List[Dict[str, Any]] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class GroupSummary(BaseModel):
    codigo_grupo: GroupCode
    total_estudiantes: int = 0
    total_docentes: int = 0

    model_config = ConfigDict(from_attributes=True)