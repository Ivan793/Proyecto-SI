from pydantic import BaseModel, Field

class SubResearchLineBase(BaseModel):
    nombre_sublinea: str = Field(
        ...,
        max_length=40,
        description=(
            "Nombre de la sub-línea de investigación. "
            "Depende de la línea principal seleccionada."
        )
    )
    codigo_linea: int = Field(
        ...,
        description=(
            "Código de la línea de investigación asociada. "
            "1: Tecnologías de la Información y la Comunicación | "
            "2: Transformación Digital"
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "nombre_sublinea": "Ingeniería de software",
                "codigo_linea": 1
            }
        }


class SubResearchLineCreate(SubResearchLineBase):
    pass


class SubResearchLineResponse(SubResearchLineBase):
    codigo_sublinea: int = Field(
        ...,
        description=(
            "Identificador único de la sublínea de investigación. "
            "Ejemplo: 1 - Sistemas de información, 2 - Ingeniería de software, etc."
        )
    )

    class Config:
        orm_mode = True
