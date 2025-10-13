from pydantic import BaseModel, Field
from typing import Optional

class GuestBase(BaseModel):
    id_usuario: str = Field(..., max_length=30)
    id_sector: str = Field(..., max_length=30)
    nombre_empresa: str = Field(..., max_length=40)


class GuestCreate(GuestBase):
    pass


class GuestResponse(GuestBase):
    id_invitado: str

    class Config:
        orm_mode = True
