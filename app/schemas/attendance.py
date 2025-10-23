from pydantic import BaseModel, Field
from datetime import datetime

from app.schemas.types import AttendanceDateTime, AttendanceId, ProjectId, UserId

class AttendanceBase(BaseModel):
    id_usuario: UserId
    id_proyecto: ProjectId
    fecha_asistencia: AttendanceDateTime

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
    id_asistencia: AttendanceId
    class Config:
        orm_mode = True
