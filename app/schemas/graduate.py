from pydantic import BaseModel, Field

class GraduateBase(BaseModel):
    id_usuario: str = Field(
        ..., 
        max_length=30, 
        description="Identificador del usuario asociado (referencia lógica a la colección usuarios)"
    )
    anio_finalizacion: str = Field(
        ..., 
        min_length=4, 
        max_length=4, 
        pattern=r"^\d{4}$", 
        description="Año en que el egresado culminó sus estudios (solo el año, ej: 2023)"
    )
    titulado: str = Field(
        ..., 
        pattern=r"^(SI|NO)$", 
        description="Indica si el egresado ha obtenido su título profesional ('SI' o 'NO')"
    )
    codigo_programa: str = Field(
        ..., 
        max_length=10, 
        description="Identificador del programa académico del cual egresó el estudiante"
    )


class GraduateCreate(GraduateBase):
    pass


class GraduateResponse(GraduateBase):
    id_egresado: str = Field(
        ..., 
        max_length=30, 
        description="Identificador único generado automáticamente por Firebase"
    )

    class Config:
        orm_mode = True
