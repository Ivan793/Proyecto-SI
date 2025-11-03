from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime

from app.schemas.types import GroupCode, StatusActive, SubjectCode, TeacherId
from app.core.constants import Defaults
from app.schemas.user import UserBasicInfo


class GroupBase(BaseModel):
    codigo_grupo: GroupCode
    id_docente: TeacherId  # Docente es obligatorio en el grupo

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_grupo": "101",
                "id_docente": "L7Tz5A23fWx19oK9jK1a"
            }
        }
    )

class GroupCreate(BaseModel):
    codigo_grupo: GroupCode
    id_docente: TeacherId

    @field_validator("codigo_grupo")
    @classmethod
    def validate_group_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("El código de grupo no puede estar vacío")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_grupo": "101",
                "id_docente": "L7Tz5A23fWx19oK9jK1a"
            }
        }
    )


class GroupUpdate(BaseModel):
    id_docente: Optional[TeacherId] = None
    codigo_grupo: Optional[GroupCode] = None
    activo: Optional[StatusActive] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_materia": "MAT101",
                "id_docente": "NEW_TEACHER_ID",
                "activo": True
            }
        }
    )



class GroupResponse(BaseModel):
    codigo_grupo: GroupCode
    id_docente: TeacherId
    activo: StatusActive = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GroupWithDetailsResponse(GroupResponse):
    """Grupo con información extendida"""
    nombre_materia: Optional[str] = None
    nombre_docente: Optional[str] = None
    # total_estudiantes: int = Field(default=0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class GroupSummary(BaseModel):
    codigo_grupo: GroupCode
    total_estudiantes: int = 0
    total_docentes: int = 0

    model_config = ConfigDict(from_attributes=True)
