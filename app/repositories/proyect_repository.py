from typing import List, Optional
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate

# Simulación de base de datos en memoria
proyectos_db: List[ProyectoResponse] = []
proyecto_id_counter = 1


def create_proyecto(proyecto: ProyectoCreate) -> ProyectoResponse:
    """
    Crea un nuevo proyecto y lo almacena en la base de datos simulada.
    """
    global proyecto_id_counter

    # Generar un ID de proyecto único simulado
    new_id = f"PRJ{proyecto_id_counter:04d}"

    new_proyecto = ProyectoResponse(
        id_proyecto=new_id,
        id_docente=proyecto.id_docente,
        id_estudiante=proyecto.id_estudiante,
        id_docente_materia=proyecto.id_docente_materia,
        codigo_linea=proyecto.codigo_linea,
        codigo_sublinea=proyecto.codigo_sublinea,
        titulo_proyecto=proyecto.titulo_proyecto,
        tipo_actividad=proyecto.tipo_actividad,
        formato_pdf=proyecto.formato_pdf,
        fecha_subida=proyecto.fecha_subida,
        calificacion=proyecto.calificacion
    )

    proyectos_db.append(new_proyecto)
    proyecto_id_counter += 1
    return new_proyecto


def list_proyectos() -> List[ProyectoResponse]:
    """
    Retorna todos los proyectos registrados.
    """
    return proyectos_db


def get_proyecto(proyecto_id: str) -> Optional[ProyectoResponse]:
    """
    Obtiene un proyecto por su ID.
    """
    for proyecto in proyectos_db:
        if proyecto.id_proyecto == proyecto_id:
            return proyecto
    return None


def update_proyecto(proyecto_id: str, proyecto: ProyectoUpdate) -> Optional[ProyectoResponse]:
    """
    Actualiza los datos de un proyecto existente.
    """
    for i, p in enumerate(proyectos_db):
        if p.id_proyecto == proyecto_id:
            updated_proyecto = p.copy(update=proyecto.dict(exclude_unset=True))
            proyectos_db[i] = updated_proyecto
            return updated_proyecto
    return None


def delete_proyecto(proyecto_id: str) -> bool:
    """
    Elimina un proyecto por su ID.
    """
    for i, p in enumerate(proyectos_db):
        if p.id_proyecto == proyecto_id:
            del proyectos_db[i]
            return True
    return False
