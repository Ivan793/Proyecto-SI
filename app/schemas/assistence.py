from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AsistenciaBase(BaseModel):
    correo_usuario: Optional[str] = Field(None, description="Correo electrónico del asistente")

    model_config = {
        "json_schema_extra": {
            "example": {
                "correo": "pinzon123@unicesar.edu.co",
            }
        }
    }


class AsistenciaCreate(AsistenciaBase):
    pass

class AsistenciaResponse(AsistenciaBase):
    id_asistencia: str = Field(..., description="Identificador único de la asistencia")
