from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.repositories.proyect_repository import ProyectoRepository
from app.exceptions.base_exceptions import AppException
from app.services.proyect_service import _validar_existencia_ids
import json

router = APIRouter(prefix="/api/v1/proyectos", tags=["Proyectos"])
repository = ProyectoRepository()


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
    - 'calificacion' siempre será null.
    - 'estado_calificacion' se guarda automáticamente como 'pendiente'.
    """
    try:
        proyecto_dict = json.loads(proyecto_data)

        # Validar estructura básica de IDs y referencias
        _validar_existencia_ids(proyecto_dict)

        # Forzar valores iniciales
        proyecto_dict["calificacion"] = None
        proyecto_dict["estado_calificacion"] = "pendiente"

        # Crear proyecto
        new_id = await repository.create_with_pdf(proyecto_dict, archivo)
        created = await repository.get_by_id(new_id)

        return ProyectoResponse(**created)

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El campo 'proyecto_data' debe ser JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
#  Listar proyectos
# ==========================================================
@router.get("/", response_model=list[ProyectoResponse])
async def list_proyectos():
    """
    Obtiene todos los proyectos activos.
    """
    proyectos = await repository.get_all()
    return [ProyectoResponse(**p) for p in proyectos]


# ==========================================================
#  Actualizar información general (NO calificación)
# ==========================================================
@router.put("/{proyect_id}", response_model=ProyectoResponse)
async def update_proyecto(
    proyect_id: str,
    proyecto_data: str = Form(...),
    archivo: UploadFile = File(None)
):
    """
    Actualiza un proyecto. El PDF es opcional.
    No permite modificar la calificación ni el estado_calificacion.
    """
    try:
        proyecto_dict = json.loads(proyecto_data)

        # Proteger campos que no deben modificarse aquí
        proyecto_dict.pop("calificacion", None)
        proyecto_dict.pop("estado_calificacion", None)

        await repository.update_with_pdf(proyect_id, proyecto_dict, archivo)
        updated = await repository.get_by_id(proyect_id)
        return ProyectoResponse(**updated)

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El campo 'proyecto_data' debe ser JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
#  Actualizar calificación y estado_calificacion
# ==========================================================
@router.put("/{proyect_id}/calificacion", response_model=ProyectoResponse)
async def actualizar_calificacion(
    proyect_id: str,
    calificacion: float = Form(...)
):
    """
    Actualiza la calificación de un proyecto.
    - Si la nota >= 3 → estado_calificacion = 'aprobado'
    - Si la nota < 3 → estado_calificacion = 'reprobado'
    - Si la nota es null → estado_calificacion = 'pendiente'
    """
    try:
        if calificacion is not None:
            if calificacion < 0 or calificacion > 5:
                raise HTTPException(status_code=400, detail="La calificación debe estar entre 0 y 5.")

            estado = "aprobado" if calificacion >= 3 else "reprobado"
        else:
            calificacion = None
            estado = "pendiente"

        update_data = {"calificacion": calificacion, "estado_calificacion": estado}
        await repository.update_with_pdf(proyect_id, update_data, archivo=None)

        updated = await repository.get_by_id(proyect_id)
        return ProyectoResponse(**updated)

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
#  Eliminado lógico
# ==========================================================
@router.delete("/{proyect_id}")
async def delete_proyecto(proyect_id: str):
    """
    Elimina lógicamente un proyecto (marca como inactivo).
    """
    try:
        success = await repository.soft_delete_proyect(proyect_id)
        if not success:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        return {"message": "Proyecto desactivado correctamente"}
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
