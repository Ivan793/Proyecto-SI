from pydantic import BaseModel
from app.schemas.types import SectorId, SectorName

class SectorBase(BaseModel):
    nombre_sector: SectorName

class SectorCreate(SectorBase):
    pass

class SectorResponse(SectorBase):
    id_sector: SectorId

    class Config:
        orm_mode = True