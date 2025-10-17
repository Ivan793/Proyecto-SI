from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.services import proyect_service


router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


@router.post("/", response_model=ProyectoResponse)
def create_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto en el sistema."""
    return proyect_service.create_proyecto(proyecto)


@router.get("/", response_model=List[ProyectoResponse])
def list_proyectos():
    """Lista todos los proyectos registrados."""
    return proyect_service.list_proyectos()


@router.get("/{proyecto_id}", response_model=ProyectoResponse)
def get_proyecto(proyecto_id: str):
    """Obtiene un proyecto específico por su ID."""
    proyecto = proyect_service.get_proyecto(proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
def update_proyecto(proyecto_id: str, proyecto: ProyectoUpdate):
    """Actualiza los datos de un proyecto existente."""
    updated = proyect_service.update_proyecto(proyecto_id, proyecto)
    if not updated:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return updated


@router.delete("/{proyecto_id}")
def delete_proyecto(proyecto_id: str):
    """Elimina un proyecto por su ID."""
    success = proyect_service.delete_proyecto(proyecto_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"message": "Proyecto eliminado correctamente"}
