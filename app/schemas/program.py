from pydantic import BaseModel, Field

class ProgramBase(BaseModel):
    nombre_programa: str = Field(
        ...,
        max_length=40,
        description=(
            "Nombre del programa académico. Ejemplo: 'Ingeniería de sistemas'."
        )
    )
    id_facultad: str = Field(
        ...,
        max_length=30,
        description=(
            "Identificador (ID del documento en Firebase) que referencia la facultad "
            "a la que pertenece el programa académico. Ejemplo: 'L7Tz5A23fWx19oK9jK1a'."
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "nombre_programa": "Ingeniería de sistemas",
                "id_facultad": "L7Tz5A23fWx19oK9jK1a"
            }
        }


class ProgramCreate(ProgramBase):
    pass


class ProgramResponse(ProgramBase):
    codigo_programa: str = Field(
        ...,
        max_length=10,
        description="Código único que identifica el programa académico. Ejemplo: '321332'."
    )

    class Config:
        orm_mode = True
