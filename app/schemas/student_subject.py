from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.schemas.types import *
from app.core.constants import Defaults


class StudentSubjectBase(BaseModel):
    id_estudiante: StudentId
    id_docente_materia: TeacherSubjectId

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_estudiante": "R9Kz4B19xUy78nQ6vT2s",
                "id_docente_materia": "K4Pq7A32dJx90nL8yH3b"
            }
        }
    )



class StudentSubjectCreate(StudentSubjectBase):
    pass



class StudentSubjectUpdate(BaseModel):
    id_estudiante: Optional[StudentId] = None
    id_docente_materia: Optional[TeacherSubjectId] = None



class StudentSubjectResponse(StudentSubjectBase):
    id_estudiante_materia: StudentSubjectId
    activo: StatusActive = Field(default=Defaults.ACTIVE_STATUS)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
