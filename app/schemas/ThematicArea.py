from pydantic import BaseModel, Field

class ThematicAreaBase(BaseModel):
    nombre_Area: str = Field(
        ...,
        max_length=50,
        description=(
            "Nombre del área temática asociada a una sublínea de investigación. "
            "Ejemplo: 'Gestión de bases de datos', 'Sistemas colaborativos'."
        )
    )
    codigo_sublinea: int = Field(
        ...,
        description=(
            "Código de la sublínea de investigación a la que pertenece el área temática. "
            "Sirve como clave foránea (FK) hacia SubResearchLine."
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "nombre_Area": "Gestión de bases de datos",
                "codigo_sublinea": 1
            }
        }


class ThematicAreaCreate(ThematicAreaBase):
    pass


class ThematicAreaResponse(ThematicAreaBase):
    codigo_area: int = Field(
        ...,
        description="Código único que identifica cada área temática. Ejemplo: 1, 2, 3, etc."
    )

    class Config:
        orm_mode = True
