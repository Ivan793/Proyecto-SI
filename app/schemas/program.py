from pydantic import BaseModel
from app.schemas.types import ProgramName, ProgramCode, FacultyId

class ProgramBase(BaseModel):
    nombre_programa: ProgramName
    id_facultad: FacultyId

    class Config:
        json_schema_extra = {
            "example": {
                "nombre_programa": "Ingeniería de sistemas",
                "id_facultad": "L7Tz5A23fWx19oK9jK1a"
            }
        }

class ProgramCreate(ProgramBase):
    pass

class ProgramResponse(ProgramBase):
    codigo_programa: ProgramCode

    class Config:
        orm_mode = True