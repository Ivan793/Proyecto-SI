from pydantic import BaseModel
from app.schemas.types import StudentId, TeacherSubjectId, StudentSubjectId

class StudentSubjectBase(BaseModel):
    id_estudiante: StudentId
    id_docente_materia: TeacherSubjectId

    class Config:
        json_schema_extra = {
            "example": {
                "id_estudiante": "A3Df7H29mLp93sN1xT8q",
                "id_docente_materia": "L7Tz5A23fWx19oK9jK1a"
            }
        }

class StudentSubjectCreate(StudentSubjectBase):
    pass

class StudentSubjectResponse(StudentSubjectBase):
    id_estudiante_materia: StudentSubjectId

    class Config:
        orm_mode = True