from pydantic import BaseModel, Field

class SubjectBase(BaseModel):
    nombre_materia: str = Field(
        ..., 
        max_length=50, 
        description="Nombre descriptivo de la materia. Ejemplo: Programación III"
    )
    ciclo_semestral: str = Field(
        ..., 
        max_length=25, 
        description="Ciclo académico al que pertenece la materia (Ej: Ciclo Básico, Profesional, Profundización)"
    )


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    codigo_materia: str = Field(
        ..., 
        max_length=8, 
        description="Identificador único de la materia, compuesto por letras y números. Ejemplo: MAT101"
    )

    class Config:
        orm_mode = True
