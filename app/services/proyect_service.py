from typing import List, Optional
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.repositories import proyect_repository


def create_proyecto(proyecto: ProyectoCreate) -> ProyectoResponse:
    """Crea un nuevo proyecto."""
    return proyect_repository.create_proyecto(proyecto)


def list_proyectos() -> List[ProyectoResponse]:
    """Devuelve la lista de todos los proyectos."""
    return proyect_repository.list_proyectos()


def get_proyecto(proyecto_id: str) -> Optional[ProyectoResponse]:
    """Obtiene un proyecto por su ID."""
    return proyect_repository.get_proyecto(proyecto_id)


def update_proyecto(proyecto_id: str, proyecto: ProyectoUpdate) -> Optional[ProyectoResponse]:
    """Actualiza un proyecto existente."""
    return proyect_repository.update_proyecto(proyecto_id, proyecto)


def delete_proyecto(proyecto_id: str) -> bool:
    """Elimina un proyecto por su ID."""
    return proyect_repository.delete_proyecto(proyecto_id)
