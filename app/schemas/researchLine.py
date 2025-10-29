from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.schemas.SubResearchLine import SubResearchLineWithAreasAdmin, SubResearchLineWithAreasPublic
from app.schemas.types import (
    ResearchLineCode, ResearchLineName
)

class ResearchLineBase(BaseModel):
    nombre_linea: ResearchLineName

class ResearchLineCreate(ResearchLineBase):
    codigo_linea: ResearchLineCode

class ResearchLineUpdate(BaseModel):
    nombre_linea: Optional[ResearchLineName] = None

class ResearchLinePublicResponse(ResearchLineBase):
    """Schema público - sin timestamps"""
    codigo_linea: ResearchLineCode
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_linea": 1,
                "nombre_linea": "Tecnologías de la Información y la comunicación"
            }
        }
    )

class ResearchLineAdminResponse(ResearchLineBase):
    """Schema administrativo - con timestamps completos"""
    codigo_linea: ResearchLineCode
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_linea": 1,
                "nombre_linea": "Tecnologías de la Información y la comunicación",
                "created_at": "2025-01-20T10:00:00Z",
                "updated_at": "2025-01-20T10:00:00Z"
            }
        }
    )

class ResearchLineWithSublinesPublic(ResearchLinePublicResponse):
    """Jerarquía pública - sin timestamps"""
    sublineas: list[SubResearchLineWithAreasPublic] = []

class ResearchLineWithSublinesAdmin(ResearchLineAdminResponse):
    """Jerarquía administrativa - con timestamps"""
    sublineas: list[SubResearchLineWithAreasAdmin] = []
