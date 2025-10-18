from pydantic import BaseModel, Field, Annotated, field_validator
from typing import Optional
from datetime import date

IdFirebase = Annotated[str, Field(min_length=5, max_length=50, description="ID generado por Firebase")]
CodigoPrograma = Annotated[int, Field(gt=0, description="Código del programa académico")]
Semestre = Annotated[int, Field(ge=1, le=10, description="Semestre actual (1-10)")]
Anio = Annotated[int, Field(ge=1950, le=2100, description="Año (ej. 2023)")]

class EstudianteBase(BaseModel):
    id_usuario: IdFirebase
    codigo_programa: CodigoPrograma
    semestre: Semestre
    anio_ingreso: Anio

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_usuario": "L7Tz5A23fWx19oK9jK1a",
                "codigo_programa": 12345,
                "semestre": 3,
                "anio_ingreso": 2023
            }
        }
    }

class EstudianteCreate(EstudianteBase):
    pass

class EstudianteUpdate(BaseModel):
    id_usuario: Optional[IdFirebase] = None
    codigo_programa: Optional[CodigoPrograma] = None
    semestre: Optional[Semestre] = None
    anio_ingreso: Optional[Anio] = None

class EstudianteResponse(EstudianteBase):
    id_estudiante: IdFirebase
