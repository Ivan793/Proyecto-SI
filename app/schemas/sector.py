from pydantic import BaseModel, Field

class SectorBase(BaseModel):
    nombre_sector: str = Field(
        ..., 
        max_length=25, 
        description="Nombre del sector (educativo, empresarial, social, gobierno)"
    )


class SectorCreate(SectorBase):
    pass


class SectorResponse(SectorBase):
    id_sector: str = Field(..., max_length=30)

    class Config:
        orm_mode = True
