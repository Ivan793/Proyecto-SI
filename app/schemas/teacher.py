from pydantic import BaseModel, Field

class TeacherBase(BaseModel):
    id_usuario: str = Field(
        ..., 
        max_length=30, 
        description="Identificador del usuario asociado al docente (referencia lógica a Usuarios)"
    )
    categoria_docente: str = Field(
        ..., 
        max_length=30, 
        pattern="^(Interno|Invitado|Externo)$",
        description="Categoría del docente: Interno, Invitado o Externo"
    )
    codigo_programa: str = Field(
        ..., 
        max_length=10, 
        description="Identificador del programa académico asignado (referencia a Programas)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_usuario": "L7Tz5A23fWx19oK9jK1a",
                "categoria_docente": "Interno",
                "codigo_programa": "1234"
            }
        }


class TeacherCreate(TeacherBase):
    """Schema for creating a new teacher"""
    pass


class TeacherResponse(TeacherBase):
    id_docente: str = Field(
        ..., 
        max_length=30, 
        description="Identificador único del docente generado automáticamente por Firebase"
    )

    class Config:
        orm_mode = True
