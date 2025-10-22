from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.constants import Limits, ValidationMessages
from app.core.enums import EventState
from app.schemas.types import TeacherId, ProgramCode, UserId

# ==================== SCHEMAS ====================

class EstudianteInfo(BaseModel):
    id_estudiante: UserId = Field(..., description="ID del estudiante asignado")
    nombre: Optional[str] = Field(None, description="Nombre del estudiante")
    email: Optional[str] = Field(None, description="Correo del estudiante")


class ProyectoBase(BaseModel):
    id_docente: TeacherId = Field(..., description="ID del docente que dirige el proyecto")
    id_estudiantes: List[EstudianteInfo] = Field(
        ..., 
        description="Lista de estudiantes vinculados al proyecto (mínimo 1)"
    )
    id_grupo: str = Field(..., description="Identificador del grupo académico")
    id_area_tematica: str = Field(..., description="Identificador del área temática")
    id_evento: str = Field(..., description="Identificador del evento")
    id_materia: str = Field(..., description="Identificador de la materia asociada")
    codigo_linea: ProgramCode = Field(..., description="Código de la línea de investigación")
    codigo_sublinea: Optional[str] = Field(None, description="Código de la sublínea")
    titulo_proyecto: str = Field(
        ..., 
        min_length=Limits.NAME_MIN, 
        max_length=150, 
        description="Título del proyecto"
    )
    tipo_actividad: str = Field(..., description="Tipo de actividad académica")
    calificacion: Optional[float] = Field(None, ge=0, le=5, description="Calificación del proyecto")


class ProyectoCreate(ProyectoBase):
    """Datos necesarios para crear un proyecto (PDF obligatorio)"""
    pass


class ProyectoUpdate(BaseModel):
    """Campos opcionales al actualizar un proyecto"""
    titulo_proyecto: Optional[str] = None
    tipo_actividad: Optional[str] = None
    calificacion: Optional[float] = None
    id_evento: Optional[str] = None
    id_area_tematica: Optional[str] = None


class ProyectoResponse(ProyectoBase):
    id_proyecto: str
    archivo_pdf: str
    fecha_subida: datetime
    activo: bool = True

    class Config:
        from_attributes = True
