from fastapi import APIRouter, HTTPException, status, Query
from app.services.graduate_service import GraduateService
from app.schemas.graduate import GraduateCreate, GraduateResponse, GraduateUpdate

router = APIRouter(
    prefix="/api/v1/admin/egresados",
    tags=["Egresados"]
)

graduate_service = GraduateService()


@router.post(
    "",
    response_model=GraduateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear egresado con usuario (CASCADA)"
)
async def create_graduate_with_user(graduate_data: GraduateCreate):
    try:
        return await graduate_service.create_graduate_with_user(graduate_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("", response_model=list[GraduateResponse], summary="Listar egresados activos")
async def get_all_graduates():
    try:
        graduates, _ = await graduate_service.get_all_graduates()
        return graduates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar egresados: {str(e)}")


@router.get("/{graduate_id}", response_model=GraduateResponse, summary="Obtener egresado por ID")
async def get_graduate(graduate_id: str):
    try:
        return await graduate_service.get_graduate(graduate_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{graduate_id}", response_model=GraduateResponse, summary="Actualizar egresado")
async def update_graduate(graduate_id: str, graduate_data: GraduateUpdate):
    try:
        return await graduate_service.update_graduate(graduate_id, graduate_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{graduate_id}", summary="Desactivar egresado")
async def deactivate_graduate(
    graduate_id: str,
    reason: str = Query("Desactivado por administrador", description="Motivo de la desactivación")
):
    try:
        await graduate_service.deactivate_graduate(graduate_id, reason)
        return {"status": "success", "message": f"Egresado {graduate_id} desactivado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
