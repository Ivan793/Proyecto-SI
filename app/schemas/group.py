"""
Esquemas Pydantic para Grupos Académicos con validación de docente
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

from app.schemas.types import SubjectCode, UserId


class GroupBase(BaseModel):
    nombre: Optional[str] = Field(None, description="Nombre del grupo")
    codigo_materia: Optional[SubjectCode] = Field(None, description="Código de la materia asociada")
    id_docente: Optional[UserId] = Field(None, description="ID del docente asignado al grupo")
    activo: Optional[bool] = Field(True, description="Indica si el grupo está activo")


class GroupCreate(GroupBase):
    nombre: str = Field(..., description="Nombre del grupo")
    codigo_materia: SubjectCode = Field(..., description="Código de la materia")
    id_docente: UserId = Field(..., description="ID del docente asignado")


class GroupUpdate(GroupBase):
    # Todos los campos son opcionales para actualizar parcialmente
    nombre: Optional[str] = None
    codigo_materia: Optional[SubjectCode] = None
    id_docente: Optional[UserId] = None
    activo: Optional[bool] = None


class GroupResponse(GroupBase):
    codigo_grupo: int = Field(..., description="Identificador único del grupo (autoincremental)")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GroupWithSubjectResponse(BaseModel):
    grupo: GroupResponse
    materia: Optional[Dict[str, Any]] = None  # Puedes poner la estructura de la materia si la tienes
