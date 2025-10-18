from pydantic import BaseModel, Field
from typing import Optional, Annotated
from app.schemas.user import UserCreate  # Usamos el modelo de usuario existente

# -------------------- TIPOS PERSONALIZADOS -------------------- #
CodigoPrograma = Annotated[str, Field(min_length=5, max_length=20, description="Código del programa académico")]
Anio = Annotated[int, Field(ge=1950, le=2100, description="Año de finalización (ej. 2023)")]
Titulado = Annotated[str, Field(pattern="^(SI|NO)$", description='"SI" o "NO"')]

# -------------------- EGRESADO BASE -------------------- #
class GraduateBase(BaseModel):
    anio_finalizacion: Anio
    titulado: Titulado
    codigo_programa: CodigoPrograma

    model_config = {
        "json_schema_extra": {
            "example": {
                "anio_finalizacion": 2022,
                "titulado": "SI",
                "codigo_programa": "PROG001"
            }
        }
    }

# -------------------- CREACIÓN EN CASCADA -------------------- #
class GraduateCreate(BaseModel):
    usuario: UserCreate
    anio_finalizacion: Anio
    titulado: Titulado
    codigo_programa: CodigoPrograma

class GraduateUpdate(BaseModel):
    anio_finalizacion: Optional[Anio] = None
    titulado: Optional[Titulado] = None
    codigo_programa: Optional[CodigoPrograma] = None

class GraduateResponse(GraduateBase):
    id_egresado: str
    id_usuario: str
