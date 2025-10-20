# app/schemas/guest.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.schemas.user import UserCreate, UserResponse


class GuestBase(BaseModel):
    id_sector: str = Field(..., min_length=5, max_length=50, description="ID del sector al que pertenece el invitado")
    nombre_empresa: str = Field(
        ...,
        min_length=2,
        max_length=60,
        pattern="^[A-Za-z0-9\\s\\-\\.]+$",
        description="Nombre de la empresa o institución"
    )

class GuestCreateWithUser(BaseModel):
    usuario: UserCreate
    id_sector: str
    nombre_empresa: str



class GuestCreateWithExistingUser(BaseModel):
    id_usuario: str
    id_sector: str
    nombre_empresa: str



class GuestUpdate(BaseModel):
    id_sector: Optional[str] = None
    nombre_empresa: Optional[str] = None
    activo: Optional[bool] = None



class GuestResponse(GuestBase):
    id_invitado: str
    id_usuario: str
    activo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GuestWithUserResponse(BaseModel):
    invitado: GuestResponse
    usuario: UserResponse
