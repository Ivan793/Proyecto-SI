from pydantic import BaseModel, Field

class FacultyBase(BaseModel):
    nombre_facultad: str = Field(
        ...,
        max_length=50,
        description="Nombre de la facultad. Ejemplo: 'Ingenierías y Tecnologías'."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "nombre_facultad": "Ingenierías y Tecnologías"
            }
        }


class FacultyCreate(FacultyBase):
    pass


class FacultyResponse(FacultyBase):
    id_facultad: str = Field(
        ...,
        max_length=30,
        description=(
            "Identificador único de la facultad, generado automáticamente. "
            "Ejemplo: 'L7Tz5A23fWx19oK9jK1a'."
        )
    )

    class Config:
        orm_mode = True
