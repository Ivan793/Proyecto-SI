from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.repositories.proyect_repository import ProyectoRepository
from app.exceptions.base_exceptions import AppException
from app.services.proyect_service import _validar_existencia_ids
import json

router = APIRouter(prefix="/api/v1/proyectos", tags=["Proyectos"])
repository = ProyectoRepository()


@router.post("/", response_model=ProyectoResponse)
async def create_proyecto(
        proyecto_data: str = Form(...),
        archivo: UploadFile = File(...),

):
    """
    Crea un nuevo proyecto con archivo PDF obligatorio.
    El campo `proyecto_data` debe ser un JSON string con la estructura de ProyectoCreate.
    """

    try:

        proyecto_dict = json.loads(proyecto_data)
        print("objeto id_docente", proyecto_dict["id_docente"])
        Validacion = _validar_existencia_ids(proyecto_dict)
        print("esta es la validacion", Validacion)
    # new_id = await repository.create_with_pdf(proyecto_dict, archivo)
    # created = await repository.get_by_id(new_id)
    # return ProyectoResponse(**created)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El campo 'proyecto_data' debe ser JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ProyectoResponse])
async def list_proyectos():
    proyectos = await repository.get_all()
    return [ProyectoResponse(**p) for p in proyectos]


@router.put("/{proyect_id}", response_model=ProyectoResponse)
async def update_proyecto(
        proyect_id: str,
        proyecto_data: str = Form(...),
        archivo: UploadFile = File(None)
):
    """
    Actualiza un proyecto. El PDF es opcional.
    """
    try:
        proyecto_dict = json.loads(proyecto_data)
        await repository.update_with_pdf(proyect_id, proyecto_dict, archivo)
        updated = await repository.get_by_id(proyect_id)
        return ProyectoResponse(**updated)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proyect_id}")
async def delete_proyecto(proyect_id: str):
    """
    Elimina lógicamente un proyecto (marca como inactivo).
    """
    success = await repository.soft_delete(proyect_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"message": "Proyecto desactivado correctamente"}