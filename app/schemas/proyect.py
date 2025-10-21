# schemas/proyecto_schema.py
from pydantic import BaseModel
from typing import Optional

class Proyecto(BaseModel):
    id_proyecto: str
    titulo: str
    descripcion: Optional[str]
    autor: Optional[str]
    asignatura_codigo: Optional[str]
    fecha_registro: Optional[str]  # ISO string
