from pydantic import BaseModel, Field
from datetime import datetime

class AttendanceBase(BaseModel):
    id_usuario: str = Field(
        ...,
        max_length=30,
        description=(
            "Identificador del usuario que realiza el escaneo del código QR. "
            "Debe corresponder a un usuario registrado en la colección 'users'."
        )
    )
    id_proyecto: str = Field(
        ...,
        max_length=30,
        description=(
            "Identificador del proyecto al que corresponde el código QR escaneado. "
            "Referencia al documento en la colección 'projects'."
        )
    )
    fecha_asistencia: datetime = Field(
        default_factory=datetime.now,
        description=(
            "Fecha y hora exacta en que se registró la asistencia. "
            "Se asigna automáticamente al momento del escaneo del código QR."
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_usuario": "U8Lp4X91rQt99pK3mD5s",
                "id_proyecto": "P4Tz5A23fWx19oK9jK1a",
                "fecha_asistencia": "2025-10-11T10:45:00"
            }
        }


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    id_asistencia: str = Field(
        ...,
        max_length=30,
        description=(
            "Identificador único de la asistencia, generado automáticamente "
            "por Firebase o el sistema al registrar el evento."
        )
    )

    class Config:
        orm_mode = True
