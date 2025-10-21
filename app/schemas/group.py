from pydantic import BaseModel
from typing import Optional

class Grupo(BaseModel):
    id_grupo: str
    nombre: Optional[str]
    semestre: Optional[str]
    capacidad: Optional[int]