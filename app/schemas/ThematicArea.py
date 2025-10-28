from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.schemas.types import (
    SubResearchLineCode,
    ThematicAreaCode, ThematicAreaName
)

class ThematicAreaBase(BaseModel):
    nombre_area: ThematicAreaName
    codigo_sublinea: SubResearchLineCode

class ThematicAreaCreate(ThematicAreaBase):
    pass

class ThematicAreaUpdate(BaseModel):
    nombre_area: Optional[ThematicAreaName] = None
    codigo_sublinea: Optional[SubResearchLineCode] = None

class ThematicAreaResponsePublic(ThematicAreaBase):
    """Schema público"""
    codigo_area: ThematicAreaCode
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_area": 1,
                "nombre_area": "Desarrollo de sistemas de información",
                "codigo_sublinea": 1
            }
        }
    )

class ThematicAreaResponseAdmin(ThematicAreaBase):
    """Schema administrativo"""
    codigo_area: ThematicAreaCode
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "codigo_area": 1,
                "nombre_area": "Desarrollo de sistemas de información",
                "codigo_sublinea": 1,
                "created_at": "2025-01-20T10:00:00Z",
                "updated_at": "2025-01-20T10:00:00Z"
            }
        }
    )
