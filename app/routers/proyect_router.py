from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.services import proyect_service
from app.exceptions.base_exceptions import AppException
import json

router = APIRouter(prefix="/api/v1/proyectos", tags=["Proyectos"])


# ==========================================================
# Crear proyecto (PDF obligatorio)
# ==========================================================
@router.post("/", response_model=ProyectoResponse)
async def create_proyecto(
    proyecto_data: str = Form(...),
    archivo: UploadFile = File(...),
):
    """
    Crea un nuevo proyecto con archivo PDF obligatorio.
    - El campo 'proyecto_data' debe ser un JSON string válido con la estructura de ProyectoCreate.
    - Para estudiantes activos: requiere id_docente, id_grupo, codigo_materia
    - Para egresados: NO requiere id_docente, id_grupo, codigo_materia, y NO puede tener calificación
    - La detección de egresado/estudiante se hace automáticamente según el rol del primer estudiante
    """
    try:
        # Parsear el JSON string
        proyecto_dict = json.loads(proyecto_data)
        
        # NO crear el schema todavía, pasar el dict directamente al service
        # El service se encargará de toda la lógica
        new_proyecto = await proyect_service.create_proyecto_from_dict(proyecto_dict, archivo)
        
        return new_proyecto

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El campo 'proyecto_data' debe ser JSON válido.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ==========================================================
# Listar proyectos
# ==========================================================
@router.get("/", response_model=list[ProyectoResponse])
async def list_proyectos(include_inactivos: bool = False):
    """
    Obtiene todos los proyectos.
    - Por defecto solo muestra proyectos activos
    - Parámetro opcional: include_inactivos=true para ver también los desactivados
    """
    try:
        proyectos = proyect_service.list_proyectos(include_inactivos=include_inactivos)
        return proyectos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar proyectos: {str(e)}")


# ==========================================================
# Obtener proyecto por ID
# ==========================================================
@router.get("/{proyecto_id}", response_model=ProyectoResponse)
async def get_proyecto(proyecto_id: str):
    """
    Obtiene un proyecto específico por su id_proyecto (ej: '001', '002').
    """
    try:
        proyecto = proyect_service.get_proyecto_by_id_proyecto(proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=404, detail=f"Proyecto '{proyecto_id}' no encontrado")
        return proyecto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyecto: {str(e)}")


# ==========================================================
# Actualizar información general (NO calificación)
# ==========================================================
@router.put("/{proyecto_id}", response_model=ProyectoResponse)
async def update_proyecto(
    proyecto_id: str,
    proyecto_data: str = Form(...),
    archivo: UploadFile = File(None)
):
    """
    Actualiza un proyecto. El PDF es opcional.
    No permite modificar la calificación, estado_calificacion, docente, estudiantes, grupo o materia.
    """
    try:
        proyecto_dict = json.loads(proyecto_data)

        # Proteger campos que no deben modificarse aquí
        campos_protegidos = ["calificacion", "estado_calificacion", "id_docente", 
                           "id_estudiantes", "id_grupo", "codigo_materia", "es_egresado"]
        for campo in campos_protegidos:
            proyecto_dict.pop(campo, None)

        # Validar con el schema de actualización
        proyecto_update = ProyectoUpdate(**proyecto_dict)
        
        # Actualizar proyecto
        updated = await proyect_service.update_proyecto(proyecto_id, proyecto_update, archivo)
        
        if not updated:
            raise HTTPException(status_code=404, detail=f"Proyecto '{proyecto_id}' no encontrado")
        
        return updated

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El campo 'proyecto_data' debe ser JSON válido.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar proyecto: {str(e)}")


# ==========================================================
# Actualizar calificación y estado_calificacion
# ==========================================================
@router.put("/{proyecto_id}/calificacion", response_model=ProyectoResponse)
async def actualizar_calificacion(
    proyecto_id: str,
    calificacion: float = Form(...)
):
    """
    Actualiza la calificación de un proyecto DE ESTUDIANTES ACTIVOS.
    - NO se puede calificar proyectos de egresados
    - Si la nota >= 3 → estado_calificacion = 'aprobado'
    - Si la nota < 3 → estado_calificacion = 'reprobado'
    - Si la nota es null → estado_calificacion = 'pendiente'
    """
    try:
        # Obtener el proyecto para verificar si es egresado
        proyecto = proyect_service.get_proyecto_by_id_proyecto(proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=404, detail=f"Proyecto '{proyecto_id}' no encontrado")
        
        # Verificar si es proyecto de egresado
        if proyecto.es_egresado:
            raise HTTPException(
                status_code=400, 
                detail="No se puede asignar calificación a proyectos de egresados"
            )

        # Validar rango de calificación
        if calificacion is not None:
            if calificacion < 0 or calificacion > 5:
                raise HTTPException(status_code=400, detail="La calificación debe estar entre 0 y 5.")

        # Crear update con solo la calificación
        update_data = ProyectoUpdate(calificacion=calificacion)
        
        # Actualizar proyecto
        updated = await proyect_service.update_proyecto(proyecto_id, update_data, archivo=None)
        
        if not updated:
            raise HTTPException(status_code=404, detail=f"Proyecto '{proyecto_id}' no encontrado")

        return updated

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar calificación: {str(e)}")


# ==========================================================
# Eliminado lógico
# ==========================================================
@router.delete("/{proyecto_id}")
async def delete_proyecto(proyecto_id: str):
    """
    Elimina lógicamente un proyecto (marca como inactivo).
    Funciona tanto para proyectos de estudiantes activos como de egresados.
    """
    try:
        success = proyect_service.delete_proyecto(proyecto_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Proyecto '{proyecto_id}' no encontrado")
        
        return {"message": "Proyecto desactivado correctamente", "id_proyecto": proyecto_id}
        
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar proyecto: {str(e)}")


# ==========================================================
# Endpoint adicional: Listar proyectos de egresados
# ==========================================================
@router.get("/egresados/lista", response_model=list[ProyectoResponse])
async def list_proyectos_egresados():
    """
    Obtiene únicamente los proyectos de egresados.
    """
    try:
        todos_proyectos = proyect_service.list_proyectos(include_inactivos=False)
        proyectos_egresados = [p for p in todos_proyectos if p.es_egresado]
        return proyectos_egresados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar proyectos de egresados: {str(e)}")


# ==========================================================
# Endpoint adicional: Listar proyectos de estudiantes activos
# ==========================================================
@router.get("/estudiantes/lista", response_model=list[ProyectoResponse])
async def list_proyectos_estudiantes():
    """
    Obtiene únicamente los proyectos de estudiantes activos (no egresados).
    """
    try:
        todos_proyectos = proyect_service.list_proyectos(include_inactivos=False)
        proyectos_estudiantes = [p for p in todos_proyectos if not p.es_egresado]
        return proyectos_estudiantes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar proyectos de estudiantes: {str(e)}")