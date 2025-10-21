from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.schemas.types import *
from app.core.constants import Defaults

class TeacherSubjectBase(BaseModel):
    id_docente: TeacherId
    codigo_materia: SubjectCode
    codigo_grupo: GroupCode
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_docente": "R9Kz4B19xUy78nQ6vT2s",
                "codigo_materia": "MAT101",
                "codigo_grupo": 202
            }
        }
    )


class TeacherSubjectCreate(TeacherSubjectBase):
    pass


class TeacherSubjectUpdate(BaseModel):
    id_docente: Optional[TeacherId] = None
    codigo_materia: Optional[SubjectCode] = None
    codigo_grupo: Optional[GroupCode] = None


class TeacherSubjectResponse(TeacherSubjectBase):
    id_docente_materia: TeacherSubjectId
    activo: StatusActive = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
