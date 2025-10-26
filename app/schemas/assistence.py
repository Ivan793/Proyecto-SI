from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AsistenciaBase(BaseModel):
    id_usuario: str = Field(..., description="ID del usuario que asiste al evento")
    correo_usuario: Optional[str] = Field(None, description="Correo electrónico del asistente")
    qrcode: Optional[str] = Field(None, description="Código QR escaneado o generado para validar asistencia")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_usuario": "user_123",
                "correo_usuario": "ana@unicesar.edu.co",
                "qrcode": "QR12345XYZ",
            }
        }
    }


class AsistenciaCreate(AsistenciaBase):
    pass

class AsistenciaResponse(AsistenciaBase):
    id_asistencia: str = Field(..., description="Identificador único de la asistencia")
