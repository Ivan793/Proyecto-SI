from pydantic import BaseModel, Field
from typing import Annotated
from app.schemas.user import UserBase  # 👈 se usa para el registro en cascada


IdSector = Annotated[str, Field(min_length=5, max_length=50, description="ID de sector en colección sectores")]
NombreEmpresa = Annotated[str, Field(min_length=2, max_length=60, pattern="^[A-Za-z0-9\\s\\-\\.]+$", description="Nombre de la empresa")]


class GuestBase(BaseModel):
    id_sector: IdSector
    nombre_empresa: NombreEmpresa


class GuestCreate(GuestBase):
    usuario: UserBase  # 👈 Aquí se recibe todo el objeto de usuario en cascada

    model_config = {
        "json_schema_extra": {
            "example": {
                "usuario": {
                    "tipo_documento": "CC",
                    "identificacion": "1009876543",
                    "nombres": "Laura",
                    "apellidos": "Torres",
                    "genero": "Mujer",
                    "identidad_sexual": "Heterosexual",
                    "fecha_nacimiento": "2002-05-12",
                    "direccion": "Calle 20 #10-33",
                    "pais": "Colombia",
                    "ciudad": "Valledupar",
                    "telefono": "+573054445555",
                    "correo": "laura.torres@unicesar.edu.co",
                    "contraseña": "Contra55#",
                    "rol": "Invitado"
                },
                "id_sector": "SEC001",
                "nombre_empresa": "InnovaTech S.A.S."
            }
        }
    }


class GuestResponse(GuestBase):
    id_invitado: str
    id_usuario: str

    class Config:
        orm_mode = True
