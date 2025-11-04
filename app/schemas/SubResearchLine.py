from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.schemas.ThematicArea import ThematicAreaResponseAdmin, ThematicAreaResponsePublic
from app.schemas.types import (
    ResearchLineCode,
    SubResearchLineCode, SubResearchLineName,
)

class SubResearchLineBase(BaseModel):
    nombre_sublinea: SubResearchLineName
    codigo_linea: ResearchLineCode

class SubResearchLineCreate(SubResearchLineBase):
    pass

class SubResearchLineUpdate(BaseModel):
    nombre_sublinea: Optional[SubResearchLineName] = None
    codigo_linea: Optional[ResearchLineCode] = None

class SubResearchLineResponsePublic(SubResearchLineBase):
    """Schema público"""
    codigo_sublinea: SubResearchLineCode
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_sublinea": 1,
                "nombre_sublinea": "Sistemas de información",
                "codigo_linea": 1
            }
        }
    )

class SubResearchLineResponseAdmin(SubResearchLineBase):
    """Schema administrativo"""
    codigo_sublinea: SubResearchLineCode
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_sublinea": 1,
                "nombre_sublinea": "Sistemas de información",
                "codigo_linea": 1,
                "created_at": "2025-01-20T10:00:00Z",
                "updated_at": "2025-01-20T10:00:00Z"
            }
        }
    )

class SubResearchLineWithAreasPublic(SubResearchLineResponsePublic):
    """Sublínea con áreas - versión pública"""
    areas_tematicas: list[ThematicAreaResponsePublic] = []

class SubResearchLineWithAreasAdmin(SubResearchLineResponseAdmin):
    """Sublínea con áreas - versión administrativa"""
    areas_tematicas: list[ThematicAreaResponseAdmin] = []

