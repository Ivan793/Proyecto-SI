from pydantic import BaseModel, Field

class TeacherSubjectBase(BaseModel):
    id_docente: str = Field(
        ...,
        max_length=50,
        description="Identificador del docente asignado (referencia lógica a Docentes)"
    )
    codigo_materia: str = Field(
        ...,
        max_length=8,
        description="Código de la materia asignada (referencia a Materias)"
    )
    codigo_grupo: int = Field(
        ...,
        description="Código del grupo asignado (referencia a Grupos)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_docente": "R9Kz4B19xUy78nQ6vT2s",
                "codigo_materia": "MAT101",
                "codigo_grupo": 202
            }
        }


class TeacherSubjectCreate(TeacherSubjectBase):
    pass


class TeacherSubjectResponse(TeacherSubjectBase):
    id_docente_materia: str = Field(
        ...,
        max_length=30,
        description="Identificador único de la asignación docente-materia-grupo, generado automáticamente por Firebase"
    )

    class Config:
        orm_mode = True
