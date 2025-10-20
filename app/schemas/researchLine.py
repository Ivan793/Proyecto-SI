from pydantic import BaseModel, Field

class ResearchLineBase(BaseModel):
    nombre_linea: str = Field(
        ...,
        max_length=40,
        description=(
            "Nombre de la línea de investigación. "
            "1: Tecnologías de la Información y la Comunicación "
            "2: Transformación Digital"
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "nombre_linea": "Tecnologías de la Información y la Comunicación"
            }
        }


class ResearchLineCreate(ResearchLineBase):
    pass


class ResearchLineResponse(ResearchLineBase):
    codigo_linea: int = Field(
        ...,
        description=(
            "Código único de la línea de investigación. "
            "1: Tecnologías de la Información y la Comunicación | "
            "2: Transformación Digital"
        )
    )

    class Config:
        orm_mode = True
