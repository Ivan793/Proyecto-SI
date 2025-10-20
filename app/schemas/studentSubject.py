from pydantic import BaseModel, Field

class StudentSubjectBase(BaseModel):
    id_estudiante: str = Field(
        ...,
        max_length=30,
        description="Identificador del estudiante inscrito en la materia (referencia lógica a Estudiantes)"
    )
    id_docente_materia: str = Field(
        ...,
        max_length=30,
        description="Identificador de la asignación Docente-Materia-Grupo (referencia a Docente_materias)"
    )

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
    id_estudiante_materia: str = Field(
        ...,
        max_length=30,
        description="Identificador único de la inscripción estudiante-materia generado automáticamente por Firebase"
    )

    class Config:
        orm_mode = True
